'use strict';
(function () {
  const status = new URLSearchParams(location.search).get('auth');
  if (['success', 'linked', 'expired', 'cancelled', 'failed', 'in_use', 'existing'].includes(status)) {
    location.replace('/app/?auth=' + encodeURIComponent(status));
  }
})();
