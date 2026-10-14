"""Read-only, manually checked editorial offers; never calls a shopping API."""
import json
import math
import re
import time
from datetime import datetime
from pathlib import Path

PROGRAM = {
    'id': 'toss-manual', 'approved': True,
    'allowedHosts': ['toss.shopping'], 'trackingMode': 'path',
    'trackingPathPattern': r'^/_m/[A-Za-z0-9]+$',
    'maxVerificationAgeHours': 24,
    'termsUrl': 'https://sharelink-docs.toss.im/help/operations/policy',
}


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.timestamp() if result.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def valid_offer(p, now):
    if not isinstance(p, dict) or p.get('sourceKind') != 'manual_editorial':
        return False
    required = ['id', 'name', 'options', 'sourceUrl', 'merchant', 'disclosure',
                'selectionReason', 'recommendedFor', 'notFor', 'priceConditions',
                'comparisonNote', 'imagePermissionSource']
    if any(not isinstance(p.get(k), str) or not p[k].strip() for k in required):
        return False
    if not re.fullmatch(r'wa-10-(?:0[1-9]|10)', p['id']):
        return False
    if not re.fullmatch(r'https://toss\.shopping/_m/[A-Za-z0-9]+', p.get('affiliateUrl', '')):
        return False
    if not p['sourceUrl'].startswith('https://sharelink.toss.im/links/products/'):
        return False
    if p.get('programId') != PROGRAM['id'] or p.get('affiliateApproved') is not True or p.get('linkVerified') is not True:
        return False
    if '수수료' not in p['disclosure'] or p.get('stock') != 'available':
        return False
    checked, expires = timestamp(p.get('lastVerifiedAt')), timestamp(p.get('expiresAt'))
    if checked is None or expires is None or not (now - 86400 <= checked <= now < expires <= checked + 86400):
        return False
    amount, quantity = p.get('totalPrice'), p.get('quantity')
    if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or n <= 0 for n in [amount, quantity]):
        return False
    if p.get('shippingVerified') is not True:
        return False
    if p.get('shippingIncludedDisplay') is True:
        if not p.get('shippingNote'):
            return False
    elif not isinstance(p.get('shipping'), (int, float)) or p['shipping'] < 0 or p.get('price', 0) + p['shipping'] != amount:
        return False
    if p.get('imagePath'):
        if p.get('imageUsageAllowed') is not True or not re.fullmatch(r'/curation/assets/manual-[a-z0-9-]+\.(?:png|jpg|jpeg|webp)', p['imagePath']):
            return False
    elif p.get('textOnly') is not True:
        return False
    return True


def merge_catalog(catalog, public_root, now=None):
    now = time.time() if now is None else now
    path = Path(public_root) / 'curation' / 'manual-products.json'
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        rows = payload['products']
        if not isinstance(rows, list) or len(rows) != 10 or len({p['id'] for p in rows}) != 10:
            raise ValueError('manual batch must contain ten unique products')
        offers = [p for p in rows if valid_offer(p, now)]
        offers = [p for p in offers if not p.get('imagePath') or (Path(public_root) / p['imagePath'].lstrip('/')).is_file()]
    except (OSError, ValueError, TypeError, KeyError):
        offers = []
    old = [p for p in catalog.get('products', []) if p.get('id') not in {r['id'] for r in offers}]
    catalog['products'] = old + offers
    catalog['programs'] = [p for p in catalog.get('programs', []) if p.get('id') != PROGRAM['id']] + ([PROGRAM] if offers else [])
    catalog.setdefault('status', {})['manualPublished'] = len(offers)
    catalog['status']['published'] = len(catalog['products'])
    if offers:
        catalog['status']['state'] = 'manual_editorial'
        catalog['providers'] = [p for p in catalog.get('providers', []) if p.get('id') != 'toss'] + [{'id': 'toss', 'reason': '수동 확인 상품 · API 미연결 · 자동 수집/게시 꺼짐'}]
    return catalog
