CREATE POLICY pilot_active_account ON public.ratings AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.staff_members AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.store_requests AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
CREATE POLICY pilot_active_account ON public.order_offers AS RESTRICTIVE FOR ALL TO authenticated USING (public.account_enabled()) WITH CHECK (public.account_enabled());
