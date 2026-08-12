-- ─────────────────────────────────────────────────────────────────
-- Table des licences
-- À exécuter dans Supabase > SQL Editor
-- ─────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS licences (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cle             text UNIQUE NOT NULL,          -- ex: ENVOI-XXXX-XXXX-XXXX
    client_nom      text NOT NULL,                 -- nom du client / établissement
    client_email    text,                          -- email du client
    statut          text NOT NULL DEFAULT 'active' -- active | suspendue | expiree
                    CHECK (statut IN ('active', 'suspendue', 'expiree')),
    date_creation   timestamptz DEFAULT now(),
    date_expiration timestamptz,                   -- NULL = pas d'expiration
    nb_activations  int DEFAULT 0,                 -- compteur d'activations
    max_activations int DEFAULT 3,                 -- machines autorisées (NULL = illimité)
    machines        jsonb DEFAULT '[]'::jsonb,     -- liste des fingerprints machines
    notes           text                           -- notes internes
);

-- Index pour lookup rapide par clé
CREATE INDEX IF NOT EXISTS idx_licences_cle ON licences(cle);

-- RLS : la table n'est accessible que via la Edge Function (service_role)
ALTER TABLE licences ENABLE ROW LEVEL SECURITY;

-- Aucun accès public direct
CREATE POLICY "no_public_access" ON licences
    FOR ALL
    TO anon, authenticated
    USING (false);

-- ─────────────────────────────────────────────────────────────────
-- Vue pour dashboard (optionnel)
-- ─────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW licences_dashboard
WITH (security_invoker = true)
AS
SELECT
    id,
    cle,
    client_nom,
    client_email,
    statut,
    date_creation::date AS creee_le,
    date_expiration::date AS expire_le,
    nb_activations,
    max_activations,
    jsonb_array_length(machines) AS machines_actives,
    notes
FROM licences
ORDER BY date_creation DESC;
