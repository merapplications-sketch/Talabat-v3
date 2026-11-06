# Local isolated test only, never a production configuration route.
import sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab
with lab.db() as c:
 c.execute("update finance_private.cash_delivery_policy set platform_amount=%s,reference=%s where store_id=%s",(int(sys.argv[1]),'DEMO allocation '+sys.argv[1],lab.STORE))
