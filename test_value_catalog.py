"""Private synthetic fixtures never appear in the public catalog or release configuration."""
import copy,json,tempfile,unittest
from pathlib import Path
import value_catalog as c

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent);self.root=Path(self.tmp.name);self.data=self.root/'data';self.public=self.root/'public'
        (self.data/'imports').mkdir(parents=True);(self.public/'curation/assets').mkdir(parents=True)
        (self.public/'curation/assets/test.webp').write_bytes(b'test-only')
        self.now=1800000000;dt=c.iso(self.now-60)
        self.source={'id':'fixture','enabled':True,'approved':True,'channelApproved':True,'approvalReference':'private test approval','redistributionAllowed':True,'priceComparisonAllowed':True,'termsUrl':'https://merchant.example/terms','adapter':'operator_import','file':'feed.json','maxCacheSeconds':600}
        self.program={'id':'fixture','approved':True,'allowedHosts':['merchant.example'],'requiredTrackingParams':['affiliate']}
        self.config={'enabled':True,'autoPublish':True,'sources':[self.source],'programs':[self.program]}
        self.row={'sku':'test-sku','option':'one','unit':'개','quantity':2,'currency':'KRW','name':'테스트 전용 상품','category':'수납','merchant':'검사용','sourceUrl':'https://merchant.example/product','sourceName':'test fixture','selectionReason':'검사용 비교','price':10000,'shipping':2000,'shippingVerified':True,'infoCheckedAt':dt,'expiresAt':c.iso(self.now+500),'stock':'available','quality':{'verified':True,'sourceUrl':'https://merchant.example/returns','returnSummary':'test','riskSummary':'test','checkedAt':dt},'popularity':{'kind':'sales_rank','verified':True,'value':3,'sourceUrl':'https://merchant.example/ranking','period':'test period','checkedAt':dt},'comparisons':[{'sku':'test-sku','option':'one','unit':'개','quantity':2,'price':11000,'shipping':2000,'sourceUrl':'https://other.example/item','verified':True,'checkedAt':dt},{'sku':'test-sku','option':'one','unit':'개','quantity':2,'price':15000,'shipping':0,'sourceUrl':'https://another.example/item','verified':True,'checkedAt':dt}],'programId':'fixture','affiliateUrl':'https://merchant.example/item?affiliate=Exact%2FValue','affiliateApproved':True,'linkVerified':True,'disclosure':'test-only disclosure','imagePath':'/curation/assets/test.webp','imageUsageAllowed':True,'imagePermissionSource':'https://merchant.example/images'}
        self.save([self.row])
    def tearDown(self):self.tmp.cleanup()
    def save(self,rows):c.atomic_json(self.data/'settings.json',self.config);c.atomic_json(self.data/'imports/feed.json',rows)
    def run_feed(self):return c.run(self.data,self.public,now=self.now)
    def products(self):return c.public_catalog(self.data,self.public,self.now)['products']
    def test_unit_cost_and_exact_link(self):
        self.assertEqual(self.run_feed()['published'],1);p=self.products()[0]
        self.assertEqual(p['totalPrice'],12000);self.assertEqual(p['unitPrice'],6000);self.assertEqual(p['affiliateUrl'],self.row['affiliateUrl'])
    def test_unverified_fields_and_reviews_cannot_publish(self):
        for field,value in [('shipping',None),('imageUsageAllowed',False),('linkVerified',False),('stock','unknown')]:
            row=copy.deepcopy(self.row);row[field]=value;self.save([row]);self.assertEqual(self.run_feed()['published'],0,field)
        row=copy.deepcopy(self.row);row['popularity']['kind']='review_count';self.save([row]);self.assertEqual(self.run_feed()['published'],0)
    def test_sku_options_and_expiry(self):
        row=copy.deepcopy(self.row);row['comparisons'][0]['option']='different';self.save([row]);self.assertEqual(self.run_feed()['published'],0)
        row=copy.deepcopy(self.row);row['expiresAt']=c.iso(self.now-1);self.save([row]);self.assertEqual(self.run_feed()['published'],0)
    def test_permissions_source_and_program(self):
        for flag in ['approved','channelApproved','redistributionAllowed','priceComparisonAllowed']:
            self.source[flag]=False;self.save([self.row]);self.assertEqual(self.run_feed()['published'],0,flag);self.source[flag]=True
        self.program['approved']=False;self.save([self.row]);self.assertEqual(self.run_feed()['published'],0)
    def test_dedupe_price_stock_updates(self):
        expensive=copy.deepcopy(self.row);expensive['price']=11000;self.save([expensive,self.row]);self.assertEqual(self.run_feed()['published'],1);self.assertEqual(self.products()[0]['price'],10000)
        self.row['price']=9000;self.save([self.row]);self.run_feed();self.assertEqual(self.products()[0]['price'],9000)
        self.row['stock']='soldout';self.save([self.row]);self.assertEqual(self.run_feed()['published'],0)
    def test_failure_preserves_only_fresh_data(self):
        self.run_feed();(self.data/'imports/feed.json').write_text('{broken',encoding='utf-8');self.assertEqual(self.run_feed()['published'],1)
        expired=c.public_catalog(self.data,self.public,self.now+1000);self.assertEqual(expired['products'],[]);self.assertEqual(c.read_json(self.data/'catalog.json',[]),[])
    def test_publish_off_dry_run_no_mutation(self):
        self.config['autoPublish']=False;self.save([self.row]);self.assertEqual(self.run_feed()['eligible'],1);self.assertEqual(self.products(),[])
        before=(self.data/'status.json').read_bytes();c.run(self.data,self.public,True,self.now);self.assertEqual((self.data/'status.json').read_bytes(),before)
        self.config['enabled']=False;self.save([self.row]);self.assertEqual(self.run_feed()['state'],'disabled')
    def test_path_restriction_and_approval_revocation(self):
        self.run_feed();self.source['redistributionAllowed']=False;self.save([self.row]);self.assertEqual(self.products(),[])
        self.source['redistributionAllowed']=True;self.source['file']='../settings.json';self.save([self.row]);self.assertEqual(self.run_feed()['connectedSources'],0)
    def test_blank_install_and_no_private_program_fields(self):
        result=c.public_catalog(self.root/'absent',self.public,self.now);self.assertEqual(result['products'],[]);self.assertFalse(result['status']['collectionEnabled'])
        self.program['secret']='test-never-public';self.save([self.row]);self.assertNotIn('secret',c.public_catalog(self.data,self.public,self.now)['programs'][0])

if __name__=='__main__':unittest.main()
