/**
 * 공포 오디오 엔진 (Web Audio — 외부 파일 없음)
 * - 저음 심박 + 앰비언트 드론 + 스팅/정전기/속삭임/HDD
 * - stage/mood/이상현상/클라이맥스/엔딩에 훅
 */
(function () {
  "use strict";

  var reduced =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduced) {
    var noop = function () {};
    window.__hauntAudio = {
      unlock: noop,
      setLevel: noop,
      pulse: noop,
      typeClick: noop,
      termBeep: noop,
      hddScratch: noop,
      rumble: noop,
      sting: noop,
      whisper: noop,
      staticBurst: noop,
      breath: noop,
      signalDrop: noop,
      dreadHit: noop,
      metal: noop,
      codeLaugh: noop,
      stopAll: noop,
      setMaster: noop,
    };
    return;
  }

  var ctx = null;
  var master = null;
  var comp = null;
  var unlocked = false;
  var level = 0; // 0 off · 1 soft · 2 mid · 3 heavy
  var beatTimer = null;
  var droneNodes = [];
  // 마스터 + 개별 게인 (기존 너무 작았음 → 크게)
  var masterVol = 1.45;
  var SFX = 2.35; // 개별 효과음 배수

  function ensureCtx() {
    if (ctx) return ctx;
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = masterVol;
    // 컴프레서를 덜 세게 — 작은 소리만 올리고 큰 타격은 덜 죽임
    comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -28;
    comp.knee.value = 18;
    comp.ratio.value = 2.2;
    comp.attack.value = 0.005;
    comp.release.value = 0.28;
    master.connect(comp);
    comp.connect(ctx.destination);
    return ctx;
  }

  function v(x) {
    return Math.max(0.0001, (x || 0) * SFX);
  }

  function out() {
    ensureCtx();
    return master;
  }

  function unlock() {
    unlocked = true;
    var c = ensureCtx();
    if (c && c.state === "suspended") {
      c.resume().catch(function () {});
    }
  }

  function now() {
    var c = ensureCtx();
    return c ? c.currentTime : 0;
  }

  function noiseBuffer(sec) {
    var c = ensureCtx();
    if (!c) return null;
    var len = Math.max(1, Math.floor(c.sampleRate * sec));
    var buf = c.createBuffer(1, len, c.sampleRate);
    var d = buf.getChannelData(0);
    for (var i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    return buf;
  }

  function playNoise(opts) {
    opts = opts || {};
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now() + (opts.delay || 0);
    var src = c.createBufferSource();
    src.buffer = noiseBuffer(opts.dur || 0.12);
    var f = c.createBiquadFilter();
    f.type = opts.filter || "bandpass";
    f.frequency.value = opts.freq || 1200;
    f.Q.value = opts.q != null ? opts.q : 0.7;
    var g = c.createGain();
    var vv = v(opts.vol != null ? opts.vol : 0.05);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(vv, t0 + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + (opts.dur || 0.12));
    src.connect(f);
    f.connect(g);
    g.connect(out());
    src.start(t0);
    src.stop(t0 + (opts.dur || 0.12) + 0.02);
  }

  /** 두꺼운 심박 (바디 + 노이즈 클릭) */
  function thump(vol, freq) {
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    vol = v(vol || 0.14);
    freq = freq || 48;

    // 바디 사인
    var osc = c.createOscillator();
    var og = c.createGain();
    var lf = c.createBiquadFilter();
    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, t0);
    osc.frequency.exponentialRampToValueAtTime(16, t0 + 0.22);
    lf.type = "lowpass";
    lf.frequency.value = 160;
    og.gain.setValueAtTime(0.0001, t0);
    og.gain.exponentialRampToValueAtTime(vol, t0 + 0.012);
    og.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.5);
    osc.connect(lf);
    lf.connect(og);
    og.connect(out());
    osc.start(t0);
    osc.stop(t0 + 0.52);

    // 서브 한 겹
    var sub = c.createOscillator();
    var sg = c.createGain();
    sub.type = "sine";
    sub.frequency.value = Math.max(22, freq * 0.5);
    sg.gain.setValueAtTime(0.0001, t0);
    sg.gain.exponentialRampToValueAtTime(vol * 0.7, t0 + 0.018);
    sg.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.58);
    sub.connect(sg);
    sg.connect(out());
    sub.start(t0);
    sub.stop(t0 + 0.6);

    // 어택 노이즈
    playNoise({
      dur: 0.05,
      freq: 200,
      filter: "lowpass",
      vol: (vol / SFX) * 0.45,
      q: 0.5,
    });
  }

  function beat() {
    if (level <= 0) return;
    var base = level === 1 ? 0.12 : level === 2 ? 0.2 : 0.32;
    thump(base, level >= 3 ? 40 : 50);
    setTimeout(function () {
      if (level <= 0) return;
      thump(base * 0.62, level >= 3 ? 34 : 42);
    }, level >= 3 ? 150 : 190);
  }

  function stopDrone() {
    droneNodes.forEach(function (n) {
      try {
        if (n.g) n.g.gain.exponentialRampToValueAtTime(0.0001, now() + 0.4);
        if (n.osc) n.osc.stop(now() + 0.5);
      } catch (e) {}
    });
    droneNodes = [];
  }

  /** 깔리는 공포 드론 (level에 따라 층 추가) */
  function startDrone() {
    stopDrone();
    var c = ensureCtx();
    if (!c || !unlocked || level <= 0) return;
    var t0 = now();
    var layers =
      level === 1
        ? [{ f: 42, v: v(0.028), type: "sine" }]
        : level === 2
          ? [
              { f: 38, v: v(0.04), type: "sine" },
              { f: 55, v: v(0.02), type: "triangle" },
              { f: 110, v: v(0.012), type: "sine" },
            ]
          : [
              { f: 32, v: v(0.055), type: "sine" },
              { f: 48, v: v(0.035), type: "triangle" },
              { f: 72, v: v(0.018), type: "sine" },
              { f: 180, v: v(0.01), type: "sawtooth" },
            ];

    layers.forEach(function (L, i) {
      var osc = c.createOscillator();
      var g = c.createGain();
      var f = c.createBiquadFilter();
      osc.type = L.type;
      osc.frequency.value = L.f;
      // 아주 느린 LFO 느낌
      try {
        var lfo = c.createOscillator();
        var lg = c.createGain();
        lfo.frequency.value = 0.07 + i * 0.03;
        lg.gain.value = L.f * 0.015;
        lfo.connect(lg);
        lg.connect(osc.frequency);
        lfo.start(t0);
        droneNodes.push({ osc: lfo, g: lg });
      } catch (e) {}
      f.type = "lowpass";
      f.frequency.value = 220 + i * 40;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(L.v, t0 + 1.2 + i * 0.3);
      osc.connect(f);
      f.connect(g);
      g.connect(out());
      osc.start(t0);
      droneNodes.push({ osc: osc, g: g });
    });

    // heavy: 아주 약한 핑크 노이즈 깔개
    if (level >= 3) {
      var src = c.createBufferSource();
      src.buffer = noiseBuffer(2);
      src.loop = true;
      var nf = c.createBiquadFilter();
      nf.type = "lowpass";
      nf.frequency.value = 400;
      var ng = c.createGain();
      ng.gain.value = v(0.02);
      src.connect(nf);
      nf.connect(ng);
      ng.connect(out());
      src.start(t0);
      droneNodes.push({ osc: src, g: ng });
    }
  }

  function scheduleBeat() {
    if (beatTimer) {
      clearTimeout(beatTimer);
      beatTimer = null;
    }
    if (level <= 0) return;

    function loop() {
      if (level <= 0) return;
      if (document.hidden) {
        beatTimer = setTimeout(loop, 2000);
        return;
      }
      // 가끔 불규칙 (공포감)
      if (level >= 2 && Math.random() > 0.88) {
        thump(0.09, 60);
        beatTimer = setTimeout(loop, 400 + Math.random() * 300);
        return;
      }
      beat();
      var gap = level === 1 ? 1280 : level === 2 ? 1020 : 780;
      gap += (Math.random() * 100) | 0;
      if (level >= 3 && Math.random() > 0.92) gap *= 0.55; // 급박
      beatTimer = setTimeout(loop, gap);
    }
    loop();
  }

  function setLevel(n, opts) {
    n = Math.max(0, Math.min(3, n | 0));
    if (opts && opts.once) {
      unlock();
      var prev = level;
      level = Math.max(n, 1);
      beat();
      level = prev;
      return;
    }
    if (n === level && !(opts && opts.force)) return;
    level = n;
    if (n > 0) unlock();
    if (n <= 0) {
      stopDrone();
      if (beatTimer) clearTimeout(beatTimer);
      beatTimer = null;
      return;
    }
    startDrone();
    scheduleBeat();
  }

  function pulse(strength) {
    unlock();
    var pv = strength === "heavy" ? 0.34 : strength === "mid" ? 0.22 : 0.14;
    thump(pv, strength === "heavy" ? 38 : 48);
    setTimeout(function () {
      thump(pv * 0.6, 36);
    }, 160);
    if (strength === "heavy") {
      playNoise({ dur: 0.1, freq: 90, filter: "lowpass", vol: 0.08 });
    }
  }

  function typeClick(kind) {
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    kind = kind || "mid";
    var bufferSize = 320;
    var noiseBuf = c.createBuffer(1, bufferSize, c.sampleRate);
    var data = noiseBuf.getChannelData(0);
    for (var i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * 0.85;
    var noise = c.createBufferSource();
    noise.buffer = noiseBuf;
    var nGain = c.createGain();
    var nFilter = c.createBiquadFilter();
    nFilter.type = "bandpass";
    nFilter.frequency.value = kind === "hard" ? 2400 : kind === "soft" ? 1300 : 1900;
    nFilter.Q.value = 0.85;
    var vol =
      kind === "space"
        ? 0.028
        : kind === "enter"
          ? 0.09
          : kind === "hard"
            ? 0.075
            : kind === "soft"
              ? 0.04
              : 0.055;
    vol = v(vol * (0.85 + Math.random() * 0.3));
    nGain.gain.setValueAtTime(vol, t0);
    nGain.gain.exponentialRampToValueAtTime(0.0001, t0 + (kind === "enter" ? 0.07 : 0.03));
    noise.connect(nFilter);
    nFilter.connect(nGain);
    nGain.connect(out());
    noise.start(t0);
    noise.stop(t0 + 0.08);

    var osc = c.createOscillator();
    var oGain = c.createGain();
    osc.type = "square";
    var f =
      kind === "enter"
        ? 170 + Math.random() * 40
        : kind === "space"
          ? 85 + Math.random() * 20
          : 850 + Math.random() * 750;
    osc.frequency.setValueAtTime(f, t0);
    osc.frequency.exponentialRampToValueAtTime(Math.max(40, f * 0.28), t0 + 0.022);
    oGain.gain.setValueAtTime(vol * 0.45, t0);
    oGain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.028);
    osc.connect(oGain);
    oGain.connect(out());
    osc.start(t0);
    osc.stop(t0 + 0.035);
  }

  function termBeep(pitch) {
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    var osc = c.createOscillator();
    var g = c.createGain();
    osc.type = "square";
    osc.frequency.value = pitch || 880;
    g.gain.setValueAtTime(v(0.1), t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.12);
    osc.connect(g);
    g.connect(out());
    osc.start(t0);
    osc.stop(t0 + 0.11);
  }

  function hddScratch() {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    for (var i = 0; i < 6; i++) {
      (function (i) {
        var start = t0 + i * 0.04;
        var bufLen = Math.floor(c.sampleRate * 0.045);
        var buf = c.createBuffer(1, bufLen, c.sampleRate);
        var data = buf.getChannelData(0);
        for (var j = 0; j < bufLen; j++) data[j] = (Math.random() * 2 - 1) * (1 - j / bufLen);
        var src = c.createBufferSource();
        src.buffer = buf;
        var f = c.createBiquadFilter();
        f.type = "bandpass";
        f.frequency.value = 1600 + Math.random() * 2800;
        f.Q.value = 0.5 + Math.random();
        var g = c.createGain();
        g.gain.setValueAtTime(v(0.06 + Math.random() * 0.04), start);
        g.gain.exponentialRampToValueAtTime(0.0001, start + 0.055);
        src.connect(f);
        f.connect(g);
        g.connect(out());
        src.start(start);
        src.stop(start + 0.06);
      })(i);
    }
    var osc = c.createOscillator();
    var og = c.createGain();
    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(58, t0);
    osc.frequency.linearRampToValueAtTime(40, t0 + 0.32);
    og.gain.setValueAtTime(v(0.035), t0);
    og.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.34);
    osc.connect(og);
    og.connect(out());
    osc.start(t0);
    osc.stop(t0 + 0.36);
  }

  function rumble(sec) {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    sec = Math.max(0.5, Math.min(5, sec || 1.6));
    var t0 = now();
    var osc = c.createOscillator();
    var g = c.createGain();
    var f = c.createBiquadFilter();
    osc.type = "sine";
    osc.frequency.value = 32 + Math.random() * 14;
    f.type = "lowpass";
    f.frequency.value = 100;
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(v(0.14), t0 + 0.16);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + sec);
    osc.connect(f);
    f.connect(g);
    g.connect(out());
    osc.start(t0);
    osc.stop(t0 + sec + 0.05);
    setTimeout(function () {
      thump(0.14, 44);
    }, 180);
    setTimeout(function () {
      thump(0.1, 38);
    }, 360);
  }

  /** 점프스케어/섬광 스팅 */
  function sting(kind) {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    kind = kind || "blood";

    // 급격한 디스코드 톤
    var freqs =
      kind === "neon"
        ? [880, 1320, 1760]
        : kind === "soft"
          ? [120, 180]
          : [55, 110, 220, 440];
    freqs.forEach(function (fq, i) {
      var o = c.createOscillator();
      var g = c.createGain();
      o.type = i % 2 ? "sawtooth" : "square";
      o.frequency.setValueAtTime(fq, t0);
      o.frequency.exponentialRampToValueAtTime(fq * 0.4, t0 + 0.12);
      var sv = v((kind === "soft" ? 0.055 : 0.1) * (1 - i * 0.12));
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(Math.max(0.001, sv), t0 + 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.2);
      o.connect(g);
      g.connect(out());
      o.start(t0);
      o.stop(t0 + 0.22);
    });
    playNoise({
      dur: 0.18,
      freq: kind === "neon" ? 3000 : 400,
      filter: kind === "neon" ? "highpass" : "bandpass",
      vol: kind === "soft" ? 0.07 : 0.12,
      q: 0.4,
    });
    thump(kind === "soft" ? 0.12 : 0.26, 36);
  }

  /** 속삭임 같은 필터 노이즈 */
  function whisper() {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    var src = c.createBufferSource();
    src.buffer = noiseBuffer(0.9);
    var bp = c.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.setValueAtTime(900, t0);
    bp.frequency.linearRampToValueAtTime(1600, t0 + 0.5);
    bp.frequency.linearRampToValueAtTime(600, t0 + 0.9);
    bp.Q.value = 4;
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(v(0.055), t0 + 0.15);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.95);
    src.connect(bp);
    bp.connect(g);
    g.connect(out());
    src.start(t0);
    src.stop(t0 + 1);
  }

  function staticBurst(ms) {
    unlock();
    playNoise({
      dur: (ms || 180) / 1000,
      freq: 2200,
      filter: "highpass",
      vol: 0.1,
      q: 0.3,
    });
    playNoise({
      dur: (ms || 180) / 1000,
      freq: 300,
      filter: "lowpass",
      vol: 0.08,
      q: 0.5,
    });
  }

  function breath() {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    var src = c.createBufferSource();
    src.buffer = noiseBuffer(1.4);
    var f = c.createBiquadFilter();
    f.type = "lowpass";
    f.frequency.setValueAtTime(500, t0);
    f.frequency.linearRampToValueAtTime(1200, t0 + 0.5);
    f.frequency.linearRampToValueAtTime(350, t0 + 1.3);
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.linearRampToValueAtTime(v(0.07), t0 + 0.35);
    g.gain.linearRampToValueAtTime(0.0001, t0 + 1.35);
    src.connect(f);
    f.connect(g);
    g.connect(out());
    src.start(t0);
    src.stop(t0 + 1.4);
  }

  /** 엔딩/신호 끊김 */
  function signalDrop() {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    // 하강 톤
    var o = c.createOscillator();
    var g = c.createGain();
    o.type = "sine";
    o.frequency.setValueAtTime(420, t0);
    o.frequency.exponentialRampToValueAtTime(40, t0 + 1.6);
    g.gain.setValueAtTime(v(0.1), t0);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.8);
    o.connect(g);
    g.connect(out());
    o.start(t0);
    o.stop(t0 + 1.85);
    staticBurst(400);
    setTimeout(function () {
      staticBurst(200);
    }, 500);
    setTimeout(function () {
      thump(0.18, 30);
    }, 900);
  }

  function dreadHit() {
    unlock();
    sting("blood");
    setTimeout(function () {
      rumble(1.2);
    }, 80);
  }

  function metal() {
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    [880, 1320, 1760, 2200].forEach(function (fq, i) {
      var o = c.createOscillator();
      var g = c.createGain();
      o.type = "square";
      o.frequency.value = fq * (0.98 + Math.random() * 0.04);
      g.gain.setValueAtTime(0.0001, t0 + i * 0.01);
      g.gain.exponentialRampToValueAtTime(v(0.055 / (i + 1)), t0 + 0.02 + i * 0.01);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.4);
      o.connect(g);
      g.connect(out());
      o.start(t0);
      o.stop(t0 + 0.42);
    });
    playNoise({ dur: 0.22, freq: 4500, filter: "highpass", vol: 0.06, q: 1.2 });
  }

  /**
   * 2페이즈: 프로그램/기계가 작게 웃는 소리
   * - 비트 깨진 디지털 ha-ha-ha (사각파 + 노이즈)
   * - 작게, 멀리서, 코드 실행되는 느낌
   */
  function codeLaugh(opts) {
    opts = opts || {};
    unlock();
    var c = ensureCtx();
    if (!c || !unlocked) return;
    var t0 = now();
    var vol = opts.vol != null ? opts.vol : 0.028;
    // 웃음 박자: 짧-짧-길 또는 랜덤 3~5회
    var bursts = 3 + Math.floor(Math.random() * 3);
    var base = 280 + Math.random() * 120;
    for (var i = 0; i < bursts; i++) {
      (function (i) {
        var t = t0 + i * (0.09 + Math.random() * 0.04);
        var o = c.createOscillator();
        var o2 = c.createOscillator();
        var g = c.createGain();
        var f = c.createBiquadFilter();
        o.type = "square";
        o2.type = "sawtooth";
        // 올라갔다 떨어지는 기계 웃음 피치
        var p0 = base * (1 + i * 0.08);
        o.frequency.setValueAtTime(p0, t);
        o.frequency.exponentialRampToValueAtTime(p0 * 1.35, t + 0.04);
        o.frequency.exponentialRampToValueAtTime(p0 * 0.85, t + 0.1);
        o2.frequency.setValueAtTime(p0 * 1.01, t);
        f.type = "bandpass";
        f.frequency.value = 900 + Math.random() * 600;
        f.Q.value = 2.5;
        var peak = v(vol * (0.7 + Math.random() * 0.4) * (1 - i * 0.08));
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(peak, t + 0.012);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.1 + (i === bursts - 1 ? 0.06 : 0));
        o.connect(f);
        o2.connect(f);
        f.connect(g);
        g.connect(out());
        o.start(t);
        o2.start(t);
        o.stop(t + 0.14);
        o2.stop(t + 0.14);
        // 짧은 디지털 글리치 클릭
        playNoise({
          delay: i * 0.09,
          dur: 0.035,
          freq: 2800 + Math.random() * 1200,
          filter: "highpass",
          vol: vol * 0.9,
          q: 1.4,
        });
      })(i);
    }
    // 끝에 작은 정적 (코드 터미널 잔향)
    playNoise({
      delay: bursts * 0.1 + 0.02,
      dur: 0.12,
      freq: 1800,
      filter: "bandpass",
      vol: vol * 0.7,
      q: 0.8,
    });
  }

  function stopAll() {
    level = 0;
    if (beatTimer) clearTimeout(beatTimer);
    beatTimer = null;
    stopDrone();
  }

  function setMaster(n) {
    // 1.0 = 기본(이미 크게 튜닝), 최대 2.0
    masterVol = Math.max(0, Math.min(2, n));
    if (master) master.gain.value = masterVol;
  }

  // ---- 이벤트 연동 ----
  document.addEventListener("haunt-diary", function (ev) {
    var d = (ev && ev.detail) || {};
    if (d.discovered) unlock();
    if (d.page === 0 && d.discovered) {
      pulse("soft");
      breath();
    } else if (d.page === 1) {
      pulse("mid");
      whisper();
    } else if (d.page >= 2) {
      pulse("heavy");
      hddScratch();
      setTimeout(function () {
        if (level < 2) setLevel(2);
      }, 200);
    }
  });

  document.addEventListener("haunt-stage", function (ev) {
    var s = ev && ev.detail && ev.detail.stage;
    if (s === 1) {
      unlock();
      pulse("soft");
    } else if (s === 2) {
      unlock();
      sting("soft");
      setTimeout(function () {
        rumble(1.4);
      }, 100);
      setLevel(2, { force: true });
    } else if (s >= 3) {
      unlock();
      dreadHit();
      setLevel(3, { force: true });
      setTimeout(breath, 400);
    }
  });

  document.addEventListener("haunt-mood", function (ev) {
    var m = ev && ev.detail && typeof ev.detail.mood === "number" ? ev.detail.mood : 0;
    if (m <= 1) {
      /* 일기 초반: 드론 없이 조용 */
      if (level > 0 && m === 0) setLevel(0);
    } else if (m === 2) setLevel(1);
    else if (m === 3) setLevel(2);
    else setLevel(3);
  });

  document.addEventListener("haunt-climax-phase", function (ev) {
    var p = ev && ev.detail && ev.detail.phase;
    unlock();
    if (p === 1) {
      setLevel(3, { force: true });
      staticBurst(300);
      rumble(1.6);
      termBeep(220);
    } else if (p === 2) {
      hddScratch();
      metal();
      termBeep(440);
    } else if (p === 3) {
      dreadHit();
      staticBurst(250);
      setTimeout(function () {
        sting("blood");
      }, 200);
    } else if (p === 4) {
      sting("neon");
      setTimeout(function () {
        sting("blood");
      }, 220);
      setTimeout(function () {
        termBeep(660);
      }, 100);
    } else if (p === 5) {
      rumble(2);
      pulse("heavy");
      termBeep(180);
    }
  });

  document.addEventListener("haunt-ending", function () {
    /* 엔딩 텍스트 끝난 뒤 — 여운 무음 유지 */
  });

  var mo = new MutationObserver(function () {
    if (document.body.classList.contains("is-haunting")) {
      unlock();
      setLevel(3, { force: true });
    }
    if (document.body.classList.contains("is-ending")) {
      stopAll();
    }
  });
  mo.observe(document.body, { attributes: true, attributeFilter: ["class"] });

  // 첫 상호작용에서 unlock (오디오 정책)
  function gest() {
    unlock();
    document.removeEventListener("pointerdown", gest, true);
    document.removeEventListener("keydown", gest, true);
  }
  document.addEventListener("pointerdown", gest, true);
  document.addEventListener("keydown", gest, true);

  window.__hauntAudio = {
    unlock: unlock,
    setLevel: setLevel,
    pulse: pulse,
    typeClick: typeClick,
    termBeep: termBeep,
    hddScratch: hddScratch,
    rumble: rumble,
    sting: sting,
    whisper: whisper,
    staticBurst: staticBurst,
    breath: breath,
    signalDrop: signalDrop,
    dreadHit: dreadHit,
    metal: metal,
    codeLaugh: codeLaugh,
    stopAll: stopAll,
    setMaster: setMaster,
  };
})();
