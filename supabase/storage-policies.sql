-- Run these in the Supabase SQL Editor after you create bucket `portfolio-media`
-- and mark it as a public bucket (Storage → bucket → Public).
--
-- Goal: anonymous visitors can READ objects only. Uploads stay in the Dashboard
-- (or any future admin tool using the service role — never put that key in HTML).

drop policy if exists "Public read portfolio-media" on storage.objects;

create policy "Public read portfolio-media"
on storage.objects
for select
to anon, authenticated
using (bucket_id = 'portfolio-media');

-- Do NOT add INSERT/UPDATE/DELETE policies for anon/authenticated here if you want
-- dashboard-only uploads for this bucket.
