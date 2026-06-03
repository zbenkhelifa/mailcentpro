// supabase/functions/gerer-abonnement/index.ts
// Deploy : supabase functions deploy gerer-abonnement --no-verify-jwt

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import Stripe from "https://esm.sh/stripe@14?target=deno";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type",
};

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return Response.json({ succes: false, message: "Méthode non autorisée." },
      { status: 405, headers: corsHeaders });
  }

  try {
    const { email } = await req.json();

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return Response.json({ succes: false, message: "Adresse email invalide." },
        { status: 400, headers: corsHeaders });
    }

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const { data: licence } = await supabase
      .from("licences")
      .select("stripe_customer_id, statut")
      .eq("client_email", email.trim().toLowerCase())
      .maybeSingle();

    if (!licence?.stripe_customer_id) {
      return Response.json({
        succes: false,
        message: "Aucun abonnement Stripe trouvé pour cet email. Les comptes essai gratuit ne sont pas gérés ici.",
      }, { status: 404, headers: corsHeaders });
    }

    const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY")!, {
      apiVersion: "2024-04-10",
      httpClient: Stripe.createFetchHttpClient(),
    });

    const session = await stripe.billingPortal.sessions.create({
      customer: licence.stripe_customer_id,
      return_url: "https://mailcentpro.web.app",
    });

    return Response.json({ succes: true, url: session.url }, { headers: corsHeaders });

  } catch (err) {
    console.error("Erreur gerer-abonnement:", err);
    return Response.json({ succes: false, message: "Erreur serveur." },
      { status: 500, headers: corsHeaders });
  }
});
