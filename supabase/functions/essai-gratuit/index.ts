// supabase/functions/essai-gratuit/index.ts
// Deploy : supabase functions deploy essai-gratuit --no-verify-jwt

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type",
};

function genererCle(): string {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const bloc = () =>
    Array.from({ length: 4 }, () =>
      chars[Math.floor(Math.random() * chars.length)]
    ).join("");
  return `ENVOI-${bloc()}-${bloc()}-${bloc()}`;
}

function dateExpiration31Jours(): string {
  const d = new Date();
  d.setDate(d.getDate() + 31);
  return d.toISOString();
}

async function envoyerEmailEssaiRappel(opts: {
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
    subject: "🔑 Votre clé d'essai MailCent Pro — rappel",
    htmlContent: `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#1e3a5f;padding:28px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">MailCent Pro</h1>
            <p style="margin:6px 0 0;color:#a8c4e0;font-size:13px;">Rappel clé d'essai</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;color:#333;">Bonjour <strong>${opts.nom}</strong>,</p>
            <p style="margin:0 0 24px;font-size:14px;color:#555;line-height:1.7;">
              Un essai gratuit est déjà en cours pour cette adresse email.
              Voici votre clé, valable jusqu'au <strong>${expire}</strong>.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f0f4f8;border-radius:8px;margin-bottom:28px;">
              <tr>
                <td style="padding:20px;text-align:center;">
                  <p style="margin:0 0 8px;font-size:11px;color:#888;text-transform:uppercase;
                            letter-spacing:1px;font-weight:600;">Votre clé d'essai</p>
                  <p style="margin:0;font-size:22px;font-weight:700;color:#1e3a5f;
                            letter-spacing:2px;font-family:monospace;">${opts.cle}</p>
                  <p style="margin:8px 0 0;font-size:12px;color:#aaa;">Valable jusqu'au ${expire}</p>
                </td>
              </tr>
            </table>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fefce8;border:1px solid #fde047;border-radius:8px;margin-bottom:20px;">
              <tr><td style="padding:14px 18px;">
                <p style="margin:0;font-size:13px;color:#713f12;line-height:1.6;">
                  ⏰ Pour continuer après le ${expire}, abonnez-vous depuis
                  <a href="https://mailcentpro.web.app/#pricing" style="color:#1e3a5f;">mailcentpro.web.app</a>.
                </p>
              </td></tr>
            </table>
            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">
              Besoin d'aide ? Répondez à cet email ou écrivez à codeappli09@gmail.com
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f0f4f8;padding:16px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:11px;color:#bbb;">MailCent Pro · Essai gratuit 1 mois</p>
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

async function envoyerEmailUpgrade(opts: { email: string; nom: string }) {
  const body = {
    sender: {
      name:  Deno.env.get("BREVO_SENDER_NAME") || "MailCent Pro",
      email: Deno.env.get("BREVO_SENDER_EMAIL")!,
    },
    to: [{ email: opts.email, name: opts.nom }],
    subject: "⏰ Votre essai MailCent Pro est expiré — passez à l'abonnement",
    htmlContent: `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:30px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:#1e3a5f;padding:28px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">MailCent Pro</h1>
            <p style="margin:6px 0 0;color:#a8c4e0;font-size:13px;">Votre essai est terminé</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;color:#333;">Bonjour <strong>${opts.nom}</strong>,</p>
            <p style="margin:0 0 24px;font-size:14px;color:#555;line-height:1.7;">
              Votre essai gratuit d'un mois est <strong>expiré</strong>.
              Pour continuer à utiliser MailCent Pro, choisissez un abonnement adapté à vos besoins.
            </p>

            <!-- CTA abonnement -->
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              <tr><td style="padding:8px 0;">
                <a href="https://mailcentpro.web.app/#pricing"
                   style="display:block;background:#1e3a5f;color:#fff;text-decoration:none;
                          font-size:15px;font-weight:700;padding:14px 24px;border-radius:8px;
                          text-align:center;">
                  🔓 Voir les forfaits &amp; s'abonner
                </a>
              </td></tr>
            </table>

            <!-- Avantages abonnement -->
            <p style="margin:0 0 12px;font-size:12px;color:#888;text-transform:uppercase;
                      letter-spacing:1px;font-weight:600;">Ce que vous obtenez avec l'abonnement</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              ${[
                "Accès illimité sans expiration",
                "Envois illimités par email SMTP",
                "Pièces jointes PDF par destinataire",
                "Mises à jour incluses",
                "Support par email",
              ].map(avantage => `
              <tr><td style="padding:5px 0;font-size:14px;color:#555;">
                ✅ ${avantage}
              </td></tr>`).join("")}
            </table>

            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:20px;">
              <tr><td style="padding:14px 18px;">
                <p style="margin:0;font-size:13px;color:#1e3a5f;line-height:1.6;">
                  💡 Un essai gratuit d'un mois est accordé une seule fois par adresse email.
                  L'abonnement annuel vous donne un accès complet sans limitation.
                </p>
              </td></tr>
            </table>

            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">
              Des questions ? Répondez à cet email ou écrivez à codeappli09@gmail.com
            </p>
          </td>
        </tr>
        <tr>
          <td style="background:#f0f4f8;padding:16px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:11px;color:#bbb;">MailCent Pro · Abonnements annuels</p>
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

async function envoyerEmailEssai(opts: {
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
    subject: "🎁 Votre essai gratuit MailCent Pro — clé de licence",
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
            <p style="margin:6px 0 0;color:#a8c4e0;font-size:13px;">Essai gratuit · 1 mois</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:32px 40px;">
            <p style="margin:0 0 16px;font-size:15px;color:#333;">Bonjour <strong>${opts.nom}</strong>,</p>
            <p style="margin:0 0 24px;font-size:14px;color:#555;line-height:1.7;">
              Voici votre clé d'essai gratuit valable <strong>1 mois</strong>.
              Saisissez-la lors du premier lancement de l'application pour activer votre accès.
            </p>

            <!-- Clé -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#f0f4f8;border-radius:8px;margin-bottom:28px;">
              <tr>
                <td style="padding:20px;text-align:center;">
                  <p style="margin:0 0 8px;font-size:11px;color:#888;text-transform:uppercase;
                            letter-spacing:1px;font-weight:600;">Votre clé d'essai</p>
                  <p style="margin:0;font-size:22px;font-weight:700;color:#1e3a5f;
                            letter-spacing:2px;font-family:monospace;">${opts.cle}</p>
                  <p style="margin:8px 0 0;font-size:12px;color:#aaa;">Valable jusqu'au ${expire}</p>
                </td>
              </tr>
            </table>

            <!-- Téléchargement -->
            <p style="margin:0 0 10px;font-size:12px;color:#888;text-transform:uppercase;
                      letter-spacing:1px;font-weight:600;">Télécharger l'application</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              ${[
                { os: "🪟 Windows", file: "MailCentPro-Windows.zip" },
                { os: " Mac",       file: "MailCentPro-Mac.zip"     },
                { os: "🐧 Linux",   file: "MailCentPro-Linux.zip"   },
              ].map(({ os, file }) => `
              <tr><td style="padding:4px 0;">
                <a href="https://github.com/zbenkhelifa/mailcentpro/releases/latest/download/${file}"
                   style="display:block;background:#f0f4f8;color:#1e3a5f;text-decoration:none;
                          font-size:14px;font-weight:600;padding:10px 16px;border-radius:6px;
                          border:1px solid #d1dce8;">⬇️ ${os}</a>
              </td></tr>`).join("")}
            </table>

            <!-- Étapes -->
            <p style="margin:0 0 12px;font-size:12px;color:#888;text-transform:uppercase;
                      letter-spacing:1px;font-weight:600;">Comment activer</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
              ${[
                "Téléchargez et lancez MailCent Pro",
                "Une fenêtre d'activation s'affiche au premier lancement",
                "Saisissez votre clé et cliquez sur <strong>Activer</strong>",
              ].map((step, i) => `
              <tr><td style="padding:6px 0;vertical-align:top;">
                <span style="display:inline-block;background:#1e3a5f;color:#fff;border-radius:50%;
                             width:22px;height:22px;text-align:center;line-height:22px;
                             font-size:12px;font-weight:700;margin-right:10px;">${i + 1}</span>
                <span style="font-size:14px;color:#555;">${step}</span>
              </td></tr>`).join("")}
            </table>

            <!-- Note essai -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="background:#fefce8;border:1px solid #fde047;border-radius:8px;margin-bottom:20px;">
              <tr><td style="padding:14px 18px;">
                <p style="margin:0;font-size:13px;color:#713f12;line-height:1.6;">
                  ⏰ <strong>Essai valable 1 mois</strong> — Pour continuer après le ${expire},
                  abonnez-vous depuis
                  <a href="https://mailcentpro.web.app/#pricing"
                     style="color:#1e3a5f;">mailcentpro.web.app</a>.
                </p>
              </td></tr>
            </table>

            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">
              Besoin d'aide ? Répondez à cet email ou écrivez à codeappli09@gmail.com
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f0f4f8;padding:16px 40px;text-align:center;border-top:1px solid #e8ecf0;">
            <p style="margin:0;font-size:11px;color:#bbb;">
              MailCent Pro · Essai gratuit 1 mois · Sans engagement ni carte bancaire
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
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return Response.json({ succes: false, message: "Méthode non autorisée." },
      { status: 405, headers: corsHeaders });
  }

  try {
    const { email, nom } = await req.json();

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return Response.json({ succes: false, message: "Adresse email invalide." },
        { status: 400, headers: corsHeaders });
    }

    const emailNormalise = email.trim().toLowerCase();
    const nomClient = (nom || emailNormalise.split("@")[0]).trim();

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    // Anti-abus : 1 essai par email
    const { data: existante } = await supabase
      .from("licences")
      .select("cle, statut, date_expiration, stripe_customer_id, client_nom")
      .eq("client_email", emailNormalise)
      .maybeSingle();

    if (existante) {
      const estEssai = !existante.stripe_customer_id;

      if (!estEssai) {
        return Response.json({
          succes: false,
          message: "Un abonnement actif existe déjà pour cet email.",
        }, { status: 409, headers: corsHeaders });
      }

      const essaiExpire = existante.date_expiration
        ? new Date(existante.date_expiration) < new Date()
        : false;

      if (essaiExpire) {
        await envoyerEmailUpgrade({
          email: emailNormalise,
          nom: existante.client_nom || nomClient,
        });
        return Response.json({
          succes: false,
          code: "essai_expire",
          message: "Votre essai gratuit est expiré. Un email avec les options d'abonnement vous a été envoyé.",
        }, { status: 409, headers: corsHeaders });
      }

      await envoyerEmailEssaiRappel({
        email: emailNormalise,
        nom: existante.client_nom || nomClient,
        cle: existante.cle,
        date_expiration: existante.date_expiration,
      });
      return Response.json({
        succes: false,
        code: "essai_existant",
        message: "Un essai gratuit est déjà actif pour cet email. Votre clé vous a été renvoyée par email.",
      }, { status: 409, headers: corsHeaders });
    }

    const cle             = genererCle();
    const date_expiration = dateExpiration31Jours();

    const { error } = await supabase.from("licences").insert({
      cle,
      client_nom:    nomClient,
      client_email:  emailNormalise,
      statut:        "active",
      date_expiration,
      max_activations: 1,
      machines:        [],
      nb_activations:  0,
      notes:           `Essai gratuit 1 mois — demandé le ${new Date().toLocaleDateString("fr-FR")}`,
    });

    if (error) {
      console.error("DB insert:", JSON.stringify(error));
      return Response.json({ succes: false, message: "Erreur serveur." },
        { status: 500, headers: corsHeaders });
    }

    await envoyerEmailEssai({
      email: emailNormalise,
      nom:   nomClient,
      cle,
      date_expiration,
    });

    console.log(`✅ Essai gratuit créé pour ${emailNormalise}`);
    return Response.json({ succes: true }, { headers: corsHeaders });

  } catch (err) {
    console.error("Erreur essai-gratuit:", err);
    return Response.json({ succes: false, message: "Erreur serveur." },
      { status: 500, headers: corsHeaders });
  }
});
