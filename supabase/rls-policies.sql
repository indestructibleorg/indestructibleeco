-- IndestructibleEco v1.0 — Row Level Security Policies
-- URI: indestructibleeco://supabase/rls
-- All tables enforce RLS — no access without policy match.
-- Tables: users, platforms, ai_jobs, yaml_documents, service_registry, governance_records

-- ─── Users ───────────────────────────────────────────────────────────

CREATE POLICY "Users can read own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can read all users"
  ON public.users FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── Platforms ───────────────────────────────────────────────────────

CREATE POLICY "Authenticated users can read platforms"
  ON public.platforms FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can insert platforms"
  ON public.platforms FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Admins can update platforms"
  ON public.platforms FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Admins can delete platforms"
  ON public.platforms FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── AI Jobs ─────────────────────────────────────────────────────────

CREATE POLICY "Users can read own jobs"
  ON public.ai_jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create jobs"
  ON public.ai_jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can read all jobs"
  ON public.ai_jobs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── YAML Documents ──────────────────────────────────────────────────

CREATE POLICY "Authenticated users can read yaml documents"
  ON public.yaml_documents FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can create yaml documents"
  ON public.yaml_documents FOR INSERT
  WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Owners can update own yaml documents"
  ON public.yaml_documents FOR UPDATE
  USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- ─── Service Registry ────────────────────────────────────────────────

CREATE POLICY "Authenticated users can read registry"
  ON public.service_registry FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage registry"
  ON public.service_registry FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── Governance Records ──────────────────────────────────────────────

CREATE POLICY "Authenticated users can read governance"
  ON public.governance_records FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "System can insert governance records"
  ON public.governance_records FOR INSERT
  WITH CHECK (auth.role() = 'service_role');
