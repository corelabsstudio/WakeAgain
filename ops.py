"""Local operator console. Run against an explicitly selected MATCH_DATA_DIR."""
import argparse
import json
from server import db,init_db,maintain

parser=argparse.ArgumentParser(description='WakeAgain 운영 도구')
parser.add_argument('action',choices=['stats','reports','support','hide','maintain'])
parser.add_argument('--id',help='숨길 작업물 ID')
args=parser.parse_args()
init_db()
if args.action=='maintain':
    maintain();print('무응답 알림·보류 처리를 실행했습니다.')
else:
    with db() as c:
        if args.action=='stats':
            result={table:c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ['users','profiles','portfolios','requests','quotes','reports','support']}
            result['events']={r[0]:r[1] for r in c.execute('SELECT event,COUNT(*) FROM events GROUP BY event')}
        elif args.action=='reports':
            result=[dict(r) for r in c.execute('SELECT r.id,r.portfolio_id,p.title,r.reason,r.created FROM reports r JOIN portfolios p ON p.id=r.portfolio_id ORDER BY r.created DESC')]
        elif args.action=='support':
            result=[dict(r) for r in c.execute('SELECT id,user_id,body,created FROM support ORDER BY created DESC')]
        else:
            if not args.id:parser.error('--id가 필요합니다.')
            result={'hidden':c.execute('UPDATE portfolios SET published=0 WHERE id=?',(args.id,)).rowcount}
        print(json.dumps(result,ensure_ascii=False,indent=2))
