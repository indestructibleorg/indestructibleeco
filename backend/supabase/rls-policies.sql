-- IndestructibleEco Supabase Row Level Security Policies
-- URI: indestructibleeco://backend/supabase/rls
-- All tables enforce RLS — no plaintext access without policy match

-- ─── Enable RLS on all tables ───
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE governance_records ENABLE ROW LEVEL SECURITY;

-- ─── Users ───
CREATE POLICY "Users can read own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Admins can read all users"
  ON users FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── Platforms ───
CREATE POLICY "Authenticated users can read platforms"
  ON platforms FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can insert platforms"
  ON platforms FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Admins can update platforms"
  ON platforms FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

CREATE POLICY "Admins can delete platforms"
  ON platforms FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── AI Jobs ───
CREATE POLICY "Users can read own jobs"
  ON ai_jobs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create jobs"
  ON ai_jobs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Admins can read all jobs"
  ON ai_jobs FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── Service Registry ───
CREATE POLICY "Authenticated users can read registry"
  ON service_registry FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "Admins can manage registry"
  ON service_registry FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- ─── Governance Records ───
CREATE POLICY "Authenticated users can read governance"
  ON governance_records FOR SELECT
  USING (auth.role() = 'authenticated');

CREATE POLICY "System can insert governance records"
  ON governance_records FOR INSERT
  WITH CHECK (auth.role() = 'service_role');