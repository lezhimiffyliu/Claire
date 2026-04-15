// Stripe Webhook Handler for Claire Pro subscriptions
// Handles: checkout.session.completed, customer.subscription.updated/deleted

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"
import Stripe from "https://esm.sh/stripe@12.0.0?target=deno"

const stripe = new Stripe(Deno.env.get("STRIPE_SECRET_KEY") as string, {
  apiVersion: "2023-10-16",
  httpClient: Stripe.createFetchHttpClient(),
})

const supabase = createClient(
  Deno.env.get("SUPABASE_URL") as string,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") as string
)

serve(async (req) => {
  const signature = req.headers.get("stripe-signature")
  const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET")

  if (!signature || !webhookSecret) {
    return new Response("Missing signature or webhook secret", { status: 400 })
  }

  try {
    const body = await req.text()
    const event = stripe.webhooks.constructEvent(body, signature, webhookSecret)

    console.log(`[webhook] Received event: ${event.type}`)

    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session
        const userId = session.metadata?.user_id
        const customerId = session.customer as string
        const subscriptionId = session.subscription as string

        if (!userId) {
          console.error("[webhook] No user_id in session metadata")
          break
        }

        // Get subscription details
        const subscription = await stripe.subscriptions.retrieve(subscriptionId)

        // Upsert payment record
        const { error } = await supabase.from("payments").upsert({
          user_id: userId,
          stripe_customer_id: customerId,
          stripe_subscription_id: subscriptionId,
          stripe_session_id: session.id,
          status: "active",
          amount: session.amount_total,
          current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
          updated_at: new Date().toISOString(),
        }, {
          onConflict: "user_id",
        })

        if (error) {
          console.error("[webhook] Error upserting payment:", error)
        } else {
          console.log(`[webhook] Activated Pro for user ${userId}`)
        }
        break
      }

      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription
        const customerId = subscription.customer as string

        // Find user by customer ID
        const { data: payment } = await supabase
          .from("payments")
          .select("user_id")
          .eq("stripe_customer_id", customerId)
          .single()

        if (payment) {
          const status = subscription.status === "active" ? "active" :
                         subscription.status === "past_due" ? "past_due" : "canceled"

          await supabase.from("payments").update({
            status,
            current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
            updated_at: new Date().toISOString(),
          }).eq("stripe_customer_id", customerId)

          console.log(`[webhook] Updated subscription status to ${status} for customer ${customerId}`)
        }
        break
      }

      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription
        const customerId = subscription.customer as string

        await supabase.from("payments").update({
          status: "canceled",
          updated_at: new Date().toISOString(),
        }).eq("stripe_customer_id", customerId)

        console.log(`[webhook] Canceled subscription for customer ${customerId}`)
        break
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { "Content-Type": "application/json" },
      status: 200,
    })

  } catch (err) {
    console.error("[webhook] Error:", err.message)
    return new Response(`Webhook Error: ${err.message}`, { status: 400 })
  }
})
