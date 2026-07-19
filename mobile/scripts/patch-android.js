/**
 * After `npx cap add/sync android` — ensure cleartext for dev + network notes.
 */
const fs = require("fs");
const path = require("path");

const androidRoot = path.join(__dirname, "..", "android");
const manifestPath = path.join(
  androidRoot,
  "app",
  "src",
  "main",
  "AndroidManifest.xml"
);
const resXml = path.join(androidRoot, "app", "src", "main", "res", "xml");
const netSec = path.join(resXml, "network_security_config.xml");

if (!fs.existsSync(manifestPath)) {
  console.log("android/ not found — run: npm run add:android");
  process.exit(0);
}

const netXml = `<?xml version="1.0" encoding="utf-8"?>
<!-- Dev: allow cleartext to LAN / emulator. Production API should be HTTPS. -->
<network-security-config>
  <base-config cleartextTrafficPermitted="false">
    <trust-anchors>
      <certificates src="system" />
    </trust-anchors>
  </base-config>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="true">10.0.2.2</domain>
    <domain includeSubdomains="true">localhost</domain>
    <domain includeSubdomains="true">127.0.0.1</domain>
    <domain includeSubdomains="true">192.168.0.0</domain>
  </domain-config>
</network-security-config>
`;

fs.mkdirSync(resXml, { recursive: true });
fs.writeFileSync(netSec, netXml, "utf8");

let man = fs.readFileSync(manifestPath, "utf8");
if (!man.includes("networkSecurityConfig")) {
  man = man.replace(
    /<application([^>]*)>/,
    '<application$1 android:networkSecurityConfig="@xml/network_security_config" android:usesCleartextTraffic="true">'
  );
  // avoid double usesCleartextTraffic
  man = man.replace(
    /android:usesCleartextTraffic="true"\s+android:usesCleartextTraffic="true"/g,
    'android:usesCleartextTraffic="true"'
  );
  fs.writeFileSync(manifestPath, man, "utf8");
  console.log("patched AndroidManifest + network_security_config");
} else {
  console.log("Android network config already present");
}
