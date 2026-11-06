import sys,pathlib,json,html,http.server
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import lab,gateway
class Handler(gateway.Handler):
 def route(self,head=False):
  if self.path.split('?')[0]=='/':
   rows=[]
   for title,file,account in [('الزبون','customer','customer'),('المطعم','merchant','merchant'),('السائق','driver','driver1'),('الإدارة','admin','admin'),('المحاسب','admin','accountant')]:
    a=lab.state()['accounts'][account];rows.append(f'<tr><td><a target="_blank" href="/{file}.html?lang=en">{title}</a></td><td>{html.escape(a["email"])}</td><td>{html.escape(a["password"])}</td></tr>')
   body=('''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>TALABOT cash lab</title><body dir=rtl style="font-family:system-ui;max-width:1050px;margin:30px auto;padding:20px"><h1>TALABOT — تجربة الكاش بالواجهات الحالية</h1><p>حسابات وأموال وهمية محلية فقط. افتح الإدارة والمحاسب بملفي متصفح منفصلين كي لا تتشارك جلساتهما. لا تستخدم بيانات أو إيصالات حقيقية.</p><p>اطلب من DEMO pilot بعنوان DEMO Rudaki 1 وإحداثيات 38.5598 و68.787. المطعم يراجع الطلب، الزبون يؤكده، الإدارة تعين السائق المتصل. السائق يستلم ثم يفتح سجل الإرجاع لتوثيق دفع 25 TJS ومرجع مستقل لكل طلب: DEMO-PAY-1 ثم DEMO-PAY-2. بعد الوصول يؤكد قبض 40 TJS والتسليم. المحاسب يسجل استلام الكاش فقط بعد استلامه افتراضياً في هذا المعمل.</p><p>المحاسب يستلم حصة المنصة فقط: 5 من التوصيل 15. السائق يحتفظ بثمن الوجبة 25 وحصته 10. لتجربة حصة السائق كاملة شغّل محلياً python tests/pilot/cash/policy.py 0 قبل الطلب الثاني: المستحق للمنصة صفر ولا تسليم للمحاسب. المطالبة الاستثنائية تبقى مفتوحة حتى تأكيد قبض الرد.</p><table cellpadding=12 border=1><tr><th>الدور</th><th>البريد</th><th>كلمة مرور المعمل</th></tr>'''+''.join(rows)+'</table>').encode()
   self.send_response(200);self.send_header('Content-Type','text/html;charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers()
   if not head:self.wfile.write(body)
   return
  return super().route(head)
http.server.ThreadingHTTPServer(('127.0.0.1',8080),Handler).serve_forever()
