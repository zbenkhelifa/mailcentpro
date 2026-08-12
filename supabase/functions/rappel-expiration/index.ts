// supabase/functions/rappel-expiration/index.ts
// Deploy : supabase functions deploy rappel-expiration --no-verify-jwt
// Déclenché chaque jour à 8h UTC via pg_cron

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

async function envoyerEmailRappelExpiration(opts: {
  email: string;
  nom: string;
  cle: string;
  date_expiration: string;
}) {
  const expire = new Date(opts.date_expiration).toLocaleDateString("fr-FR");

  const body = {
    sender: {
      name:  Deno.env.get("BREVO_SENDER_NAME") || "MailCent Pro",
      email: Deno.env.get("BREVO_SENDER_EMAIL")!,
    },
    to: [{ email: opts.email, name: opts.nom }],
    subject: "⏰ Votre essai MailCent Pro expire demain",
    htmlContent: `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#1e3a5f;padding:28px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">MailCent Pro</h1>
            <p style="margin:6px 0 0;color:#fbbf24;font-size:13px;font-weight:600;">⏰ Votre essai expire demain</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;color:#333;">Bonjour <strong>${opts.nom}</strong>,</p>
            <p style="margin:0 0 24px;font-size:14px;color:#555;line-height:1.7;">
              Votre essai gratuit MailCent Pro se termine le <strong>${expire}</strong>, soit <strong>demain</strong>.
              Pour continuer à envoyer vos emails sans interruption, abonnez-vous dès maintenant.
            </p>

            <!-- Urgence -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;margin-bottom:28px;">
              <tr><td style="padding:16px 20px;text-align:center;">
                <p style="margin:0;font-size:16px;font-weight:700;color:#92400e;">
                  ⏰ Plus qu'1 jour pour s'abonner
                </p>
                <p style="margin:6px 0 0;font-size:13px;color:#78350f;">
                  Votre clé <code style="font-family:monospace;font-weight:700;">${opts.cle}</code>
                  expirera le ${expire}
                </p>
              </td></tr>
            </table>

            <!-- CTA -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              <tr><td style="padding:4px 0;">
                <a href="https://mailcentpro.web.app/#pricing"
                   style="display:block;background:#1e3a5f;color:#fff;text-decoration:none;
                          font-size:15px;font-weight:700;padding:14px 24px;border-radius:8px;
                          text-align:center;">
                  🔓 Voir les forfaits &amp; s'abonner
                </a>
              </td></tr>
            </table>

            <!-- Avantages -->
            <p style="margin:0 0 12px;font-size:12px;color:#888;text-transform:uppercase;
                      letter-spacing:1px;font-weight:600;">Avec l'abonnement vous continuez à</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              ${[
                "Envoyer des emails personnalisés en masse",
                "Joindre des PDF différents par destinataire",
                "Importer vos listes CSV",
                "Profiter des mises à jour et du support",
              ].map(a => `
              <tr><td style="padding:5px 0;font-size:14px;color:#555;">✅ ${a}</td></tr>`).join("")}
            </table>

            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">
              Des questions ? Répondez à cet email ou écrivez à codeappli09@gmail.com
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f0f4f8;padding:16px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:11px;color:#bbb;">
              MailCent Pro · Abonnements annuels · mailcentpro.web.app
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`,
  };

  const resp = await fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": Deno.env.get("BREVO_API_KEY")!,
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`Brevo ${resp.status}: ${err}`);
  }
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response("Méthode non autorisée", { status: 405 });
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // Essais gratuits qui expirent demain, rappel pas encore envoyé
  const demain = new Date();
  demain.setDate(demain.getDate() + 1);
  const dateDebut = new Date(demain);
  dateDebut.setHours(0, 0, 0, 0);
  const dateFin = new Date(demain);
  dateFin.setHours(23, 59, 59, 999);

  const { data: licences, error } = await supabase
    .from("licences")
    .select("id, cle, client_nom, client_email, date_expiration")
    .is("stripe_customer_id", null)
    .eq("statut", "active")
    .gte("date_expiration", dateDebut.toISOString())
    .lte("date_expiration", dateFin.toISOString())
    .eq("rappel_expiration_envoye", false);

  if (error) {
    console.error("Erreur requête licences:", error);
    return new Response("Erreur DB", { status: 500 });
  }

  if (!licences || licences.length === 0) {
    console.log("Aucun essai n'expire demain.");
    return new Response("OK — aucun rappel à envoyer", { status: 200 });
  }

  let envoyes = 0;
  for (const licence of licences) {
    try {
      await envoyerEmailRappelExpiration({
        email: licence.client_email,
        nom:   licence.client_nom,
        cle:   licence.cle,
        date_expiration: licence.date_expiration,
      });

      await supabase
        .from("licences")
        .update({ rappel_expiration_envoye: true })
        .eq("id", licence.id);

      envoyes++;
      console.log(`✅ Rappel envoyé à ${licence.client_email}`);
    } catch (err) {
      console.error(`Erreur rappel pour ${licence.client_email}:`, err);
    }
  }

  return new Response(`OK — ${envoyes} rappel(s) envoyé(s)`, { status: 200 });
});
