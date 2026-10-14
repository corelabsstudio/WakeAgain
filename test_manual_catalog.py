import copy,json,tempfile,time,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
import manual_catalog as m

class ManualTest(unittest.TestCase):
    def setUp(self):
        self.now=time.time()
        self.row={'id':'wa-10-01','name':'private fixture','options':'fixture','sourceUrl':'https://sharelink.toss.im/links/products/1','merchant':'fixture','disclosure':'제휴 수수료 고지','selectionReason':'fixture','recommendedFor':'fixture','notFor':'fixture','priceConditions':'fixture','comparisonNote':'fixture','imagePermissionSource':'https://example.com/fixture','sourceKind':'manual_editorial','affiliateUrl':'https://toss.shopping/_m/PrivateFixture','programId':'toss-manual','affiliateApproved':True,'linkVerified':True,'stock':'available','lastVerifiedAt':datetime.fromtimestamp(self.now-30,timezone.utc).isoformat(),'expiresAt':datetime.fromtimestamp(self.now+300,timezone.utc).isoformat(),'totalPrice':1100,'quantity':2,'price':1000,'shipping':100,'shippingVerified':True,'textOnly':True}
    def test_valid_and_fail_closed(self):
        self.assertTrue(m.valid_offer(self.row,self.now))
        for change in [{'shipping':None},{'totalPrice':1200},{'affiliateUrl':'https://evil.example/_m/PrivateFixture'},{'disclosure':''},{'linkVerified':False},{'lastVerifiedAt':'2026-10-14T15:00:00'},{'stock':'unknown'},{'imagePath':'/curation/assets/../../private.png'},{'imagePath':'/curation/assets/manual-fixture.png','imageUsageAllowed':False}]:
            with self.subTest(change=change):
                self.assertFalse(m.valid_offer({**self.row,**change},self.now))
    def test_time_bounds(self):
        for offset in [-86401,30]:
            r={**self.row,'lastVerifiedAt':datetime.fromtimestamp(self.now+offset,timezone.utc).isoformat()}
            self.assertFalse(m.valid_offer(r,self.now))
        self.assertFalse(m.valid_offer(self.row,self.now+86400))
    def test_displayed_shipping_total(self):
        r={**self.row,'shipping':None,'shippingIncludedDisplay':True,'shippingNote':'Observed displayed total includes shipping'}
        self.assertTrue(m.valid_offer(r,self.now))
        self.assertFalse(m.valid_offer({**r,'shippingNote':''},self.now))
    def test_deployment_contains_reader(self):
        docker=(Path(__file__).parent/'Dockerfile').read_text(encoding='utf-8')
        self.assertTrue(any(line.startswith('COPY ') and 'manual_catalog.py' in line for line in docker.splitlines()))
    def test_batch_unique_and_expiry_without_auto_collection(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root=Path(tmp);(root/'curation').mkdir()
            rows=[{**self.row,'id':f'wa-10-{i:02d}'} for i in range(1,11)]
            path=root/'curation/manual-products.json';path.write_text(json.dumps({'products':rows}),encoding='utf-8')
            cat={'products':[],'programs':[],'providers':[],'status':{'collectionEnabled':False,'autoPublish':False}}
            result=m.merge_catalog(copy.deepcopy(cat),root,self.now)
            self.assertEqual(len(result['products']),10)
            self.assertFalse(result['status']['collectionEnabled']);self.assertFalse(result['status']['autoPublish'])
            self.assertEqual(m.merge_catalog(copy.deepcopy(cat),root,self.now+86400)['products'],[])
            rows[-1]['id']=rows[0]['id'];path.write_text(json.dumps({'products':rows}),encoding='utf-8')
            self.assertEqual(m.merge_catalog(copy.deepcopy(cat),root,self.now)['products'],[])

if __name__=='__main__':unittest.main()
