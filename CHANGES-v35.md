# v35 (fix/role-redirect-v35)
- The message "Этот аккаунт не подходит для этого приложения" appears when an account opens an app of another role (each app accepts only its own role: admin.html=admin, merchant.html=merchant, driver.html=driver, customer.html=customer). That is by design, but the screen was unclear.
- Now the screen says which role the account has and shows an "Open the <role> app" button that goes to the right page, plus Sign out.
- Staff accounts (patch 26) are unaffected: they still enter admin.html.
- tools/smoke.py: 3 new scenarios (admin in customer app, merchant in admin app, admin in driver app).
No SQL.
