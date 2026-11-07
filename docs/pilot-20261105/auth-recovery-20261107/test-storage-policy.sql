-- Test-only repair. No data mutation or privilege expansion.
ALTER POLICY pilot_media_insert ON storage.objects WITH CHECK (bucket_id = 'media' AND (storage.foldername(name))[1] = auth.uid()::text AND (public.is_admin() OR public.has_perm('stores') OR public.has_perm('content') OR EXISTS (SELECT 1 FROM public.stores s WHERE public.owns_store(s.id))));
