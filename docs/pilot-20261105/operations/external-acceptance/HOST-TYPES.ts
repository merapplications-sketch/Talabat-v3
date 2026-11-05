export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.18"
  }
  public: {
    Tables: {
      addresses: {
        Row: {
          apartment: string | null
          created_at: string
          details: string | null
          entrance: string | null
          floor: string | null
          house: string | null
          id: string
          is_default: boolean
          label: string
          lat: number
          lng: number
          note: string | null
          street: string
          user_id: string
        }
        Insert: {
          apartment?: string | null
          created_at?: string
          details?: string | null
          entrance?: string | null
          floor?: string | null
          house?: string | null
          id?: string
          is_default?: boolean
          label?: string
          lat: number
          lng: number
          note?: string | null
          street: string
          user_id: string
        }
        Update: {
          apartment?: string | null
          created_at?: string
          details?: string | null
          entrance?: string | null
          floor?: string | null
          house?: string | null
          id?: string
          is_default?: boolean
          label?: string
          lat?: number
          lng?: number
          note?: string | null
          street?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "addresses_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      app_pages: {
        Row: {
          body_en: string
          body_ru: string
          slug: string
          updated_at: string
          updated_by: string | null
        }
        Insert: {
          body_en?: string
          body_ru?: string
          slug: string
          updated_at?: string
          updated_by?: string | null
        }
        Update: {
          body_en?: string
          body_ru?: string
          slug?: string
          updated_at?: string
          updated_by?: string | null
        }
        Relationships: []
      }
      app_settings: {
        Row: {
          key: string
          updated_at: string
          updated_by: string | null
          value: number
        }
        Insert: {
          key: string
          updated_at?: string
          updated_by?: string | null
          value: number
        }
        Update: {
          key?: string
          updated_at?: string
          updated_by?: string | null
          value?: number
        }
        Relationships: []
      }
      app_texts: {
        Row: {
          key: string
          updated_at: string
          updated_by: string | null
          value: string
        }
        Insert: {
          key: string
          updated_at?: string
          updated_by?: string | null
          value?: string
        }
        Update: {
          key?: string
          updated_at?: string
          updated_by?: string | null
          value?: string
        }
        Relationships: []
      }
      audit_log: {
        Row: {
          action: string
          at: string
          details: Json
          id: number
          row_id: string | null
          table_name: string
          user_id: string | null
        }
        Insert: {
          action: string
          at?: string
          details?: Json
          id?: never
          row_id?: string | null
          table_name: string
          user_id?: string | null
        }
        Update: {
          action?: string
          at?: string
          details?: Json
          id?: never
          row_id?: string | null
          table_name?: string
          user_id?: string | null
        }
        Relationships: []
      }
      banners: {
        Row: {
          created_at: string
          ends_at: string | null
          id: string
          image_url: string | null
          is_active: boolean
          link_type: string
          link_value: string | null
          placement: string
          sort: number
          starts_at: string | null
          title: string
        }
        Insert: {
          created_at?: string
          ends_at?: string | null
          id?: string
          image_url?: string | null
          is_active?: boolean
          link_type?: string
          link_value?: string | null
          placement?: string
          sort?: number
          starts_at?: string | null
          title: string
        }
        Update: {
          created_at?: string
          ends_at?: string | null
          id?: string
          image_url?: string | null
          is_active?: boolean
          link_type?: string
          link_value?: string | null
          placement?: string
          sort?: number
          starts_at?: string | null
          title?: string
        }
        Relationships: []
      }
      brands: {
        Row: {
          created_at: string
          id: string
          name: string
          owner_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          name: string
          owner_id: string
        }
        Update: {
          created_at?: string
          id?: string
          name?: string
          owner_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "brands_owner_id_fkey"
            columns: ["owner_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      client_errors: {
        Row: {
          app: string | null
          at: string
          context: string | null
          id: number
          message: string | null
          ua: string | null
          user_id: string | null
        }
        Insert: {
          app?: string | null
          at?: string
          context?: string | null
          id?: never
          message?: string | null
          ua?: string | null
          user_id?: string | null
        }
        Update: {
          app?: string | null
          at?: string
          context?: string | null
          id?: never
          message?: string | null
          ua?: string | null
          user_id?: string | null
        }
        Relationships: []
      }
      favorites: {
        Row: {
          created_at: string
          store_id: string
          user_id: string
        }
        Insert: {
          created_at?: string
          store_id: string
          user_id: string
        }
        Update: {
          created_at?: string
          store_id?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "favorites_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "favorites_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      group_items: {
        Row: {
          created_at: string
          group_id: string
          id: number
          item_id: string
          note: string | null
          options: Json
          qty: number
          user_id: string
          user_name: string
        }
        Insert: {
          created_at?: string
          group_id: string
          id?: never
          item_id: string
          note?: string | null
          options?: Json
          qty: number
          user_id: string
          user_name: string
        }
        Update: {
          created_at?: string
          group_id?: string
          id?: never
          item_id?: string
          note?: string | null
          options?: Json
          qty?: number
          user_id?: string
          user_name?: string
        }
        Relationships: [
          {
            foreignKeyName: "group_items_group_id_fkey"
            columns: ["group_id"]
            isOneToOne: false
            referencedRelation: "group_orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "group_items_item_id_fkey"
            columns: ["item_id"]
            isOneToOne: false
            referencedRelation: "menu_items"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "group_items_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      group_orders: {
        Row: {
          closed_at: string | null
          created_at: string
          expires_at: string
          host_id: string
          id: string
          order_id: number | null
          status: string
          store_id: string
        }
        Insert: {
          closed_at?: string | null
          created_at?: string
          expires_at?: string
          host_id: string
          id?: string
          order_id?: number | null
          status?: string
          store_id: string
        }
        Update: {
          closed_at?: string | null
          created_at?: string
          expires_at?: string
          host_id?: string
          id?: string
          order_id?: number | null
          status?: string
          store_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "group_orders_host_id_fkey"
            columns: ["host_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "group_orders_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "group_orders_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
        ]
      }
      happy_hours: {
        Row: {
          active: boolean
          created_at: string
          created_by: string | null
          days: number[]
          discount_pct: number
          end_time: string
          id: number
          start_time: string
          store_id: string | null
          title: string
        }
        Insert: {
          active?: boolean
          created_at?: string
          created_by?: string | null
          days?: number[]
          discount_pct: number
          end_time: string
          id?: never
          start_time: string
          store_id?: string | null
          title: string
        }
        Update: {
          active?: boolean
          created_at?: string
          created_by?: string | null
          days?: number[]
          discount_pct?: number
          end_time?: string
          id?: never
          start_time?: string
          store_id?: string | null
          title?: string
        }
        Relationships: [
          {
            foreignKeyName: "happy_hours_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
        ]
      }
      item_option_groups: {
        Row: {
          created_at: string
          id: string
          item_id: string
          max_sel: number
          name: string
          required: boolean
          sort: number
        }
        Insert: {
          created_at?: string
          id?: string
          item_id: string
          max_sel?: number
          name: string
          required?: boolean
          sort?: number
        }
        Update: {
          created_at?: string
          id?: string
          item_id?: string
          max_sel?: number
          name?: string
          required?: boolean
          sort?: number
        }
        Relationships: [
          {
            foreignKeyName: "item_option_groups_item_id_fkey"
            columns: ["item_id"]
            isOneToOne: false
            referencedRelation: "menu_items"
            referencedColumns: ["id"]
          },
        ]
      }
      item_options: {
        Row: {
          available: boolean
          group_id: string
          id: string
          name: string
          price_delta: number
          sort: number
        }
        Insert: {
          available?: boolean
          group_id: string
          id?: string
          name: string
          price_delta?: number
          sort?: number
        }
        Update: {
          available?: boolean
          group_id?: string
          id?: string
          name?: string
          price_delta?: number
          sort?: number
        }
        Relationships: [
          {
            foreignKeyName: "item_options_group_id_fkey"
            columns: ["group_id"]
            isOneToOne: false
            referencedRelation: "item_option_groups"
            referencedColumns: ["id"]
          },
        ]
      }
      loyalty_ledger: {
        Row: {
          created_at: string
          id: number
          kind: string
          order_id: number | null
          points: number
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: never
          kind: string
          order_id?: number | null
          points: number
          user_id: string
        }
        Update: {
          created_at?: string
          id?: never
          kind?: string
          order_id?: number | null
          points?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "loyalty_ledger_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "loyalty_ledger_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      loyalty_lots: {
        Row: {
          created_at: string
          expires_at: string
          id: number
          kind: string
          order_id: number | null
          points: number
          points_left: number
          user_id: string
        }
        Insert: {
          created_at?: string
          expires_at: string
          id?: never
          kind: string
          order_id?: number | null
          points: number
          points_left: number
          user_id: string
        }
        Update: {
          created_at?: string
          expires_at?: string
          id?: never
          kind?: string
          order_id?: number | null
          points?: number
          points_left?: number
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "loyalty_lots_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "loyalty_lots_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      menu_items: {
        Row: {
          approved: boolean
          available: boolean
          created_at: string
          discount_pct: number
          id: string
          image_url: string | null
          name: string
          popular: boolean
          price: number
          section: string | null
          store_id: string
        }
        Insert: {
          approved?: boolean
          available?: boolean
          created_at?: string
          discount_pct?: number
          id?: string
          image_url?: string | null
          name: string
          popular?: boolean
          price: number
          section?: string | null
          store_id: string
        }
        Update: {
          approved?: boolean
          available?: boolean
          created_at?: string
          discount_pct?: number
          id?: string
          image_url?: string | null
          name?: string
          popular?: boolean
          price?: number
          section?: string | null
          store_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "menu_items_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
        ]
      }
      order_chat: {
        Row: {
          body: string
          created_at: string
          id: number
          order_id: number
          sender_id: string
        }
        Insert: {
          body: string
          created_at?: string
          id?: never
          order_id: number
          sender_id: string
        }
        Update: {
          body?: string
          created_at?: string
          id?: never
          order_id?: number
          sender_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_chat_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "order_chat_sender_id_fkey"
            columns: ["sender_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      order_customer_phone: {
        Row: {
          order_id: number
          phone: string
        }
        Insert: {
          order_id: number
          phone: string
        }
        Update: {
          order_id?: number
          phone?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_customer_phone_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: true
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      order_driver_phone: {
        Row: {
          order_id: number
          phone: string
        }
        Insert: {
          order_id: number
          phone: string
        }
        Update: {
          order_id?: number
          phone?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_driver_phone_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: true
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      order_events: {
        Row: {
          at: string
          id: number
          kind: string
          order_id: number
        }
        Insert: {
          at?: string
          id?: never
          kind: string
          order_id: number
        }
        Update: {
          at?: string
          id?: never
          kind?: string
          order_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "order_events_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      order_items: {
        Row: {
          id: string
          item_id: string | null
          name: string
          note: string | null
          options: Json
          order_id: number
          price: number
          qty: number
        }
        Insert: {
          id?: string
          item_id?: string | null
          name: string
          note?: string | null
          options?: Json
          order_id: number
          price: number
          qty: number
        }
        Update: {
          id?: string
          item_id?: string | null
          name?: string
          note?: string | null
          options?: Json
          order_id?: number
          price?: number
          qty?: number
        }
        Relationships: [
          {
            foreignKeyName: "order_items_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      order_offers: {
        Row: {
          dist_km: number | null
          driver_id: string
          expires_at: string
          id: number
          mode: string
          offered_at: string
          order_id: number
          rank: number
          state: string
        }
        Insert: {
          dist_km?: number | null
          driver_id: string
          expires_at: string
          id?: never
          mode?: string
          offered_at?: string
          order_id: number
          rank?: number
          state?: string
        }
        Update: {
          dist_km?: number | null
          driver_id?: string
          expires_at?: string
          id?: never
          mode?: string
          offered_at?: string
          order_id?: number
          rank?: number
          state?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_offers_driver_id_fkey"
            columns: ["driver_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "order_offers_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      order_recipient: {
        Row: {
          name: string
          order_id: number
          phone: string
        }
        Insert: {
          name: string
          order_id: number
          phone: string
        }
        Update: {
          name?: string
          order_id?: number
          phone?: string
        }
        Relationships: [
          {
            foreignKeyName: "order_recipient_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: true
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      orders: {
        Row: {
          address: string | null
          arrived_cust_at: string | null
          arrived_store_at: string | null
          cancel_note: string | null
          cancel_reason: string | null
          cancelled_by: string | null
          cash_collected: number | null
          cash_note: string | null
          cash_settled_at: string | null
          cashback: number
          client_key: string | null
          commission: number
          commission_pct: number
          created_at: string
          customer_id: string
          customer_name: string | null
          customer_phone: string | null
          delivery_base: number | null
          delivery_extra: number
          delivery_fee: number
          delivery_km: number | null
          delivery_photo: string | null
          discount: number
          done_at: string | null
          driver_id: string | null
          driver_name: string | null
          driver_payout: number
          fee_waived: number
          group_id: string | null
          hh_discount: number
          hh_pct: number
          id: number
          is_gift: boolean
          lat: number | null
          leave_at_door: boolean
          lng: number | null
          loyalty_done_at: string | null
          payment: string | null
          points_earned: number
          points_returned_at: string | null
          points_used: number
          points_value: number
          prep_time: number
          promo_code: string | null
          promo_discount: number
          scheduled_for: string | null
          status: Database["public"]["Enums"]["order_status"]
          store_id: string
          substitution: string
          subtotal: number
          tip: number
          total: number
          wallet_returned_at: string | null
          wallet_used: number
        }
        Insert: {
          address?: string | null
          arrived_cust_at?: string | null
          arrived_store_at?: string | null
          cancel_note?: string | null
          cancel_reason?: string | null
          cancelled_by?: string | null
          cash_collected?: number | null
          cash_note?: string | null
          cash_settled_at?: string | null
          cashback?: number
          client_key?: string | null
          commission?: number
          commission_pct?: number
          created_at?: string
          customer_id: string
          customer_name?: string | null
          customer_phone?: string | null
          delivery_base?: number | null
          delivery_extra?: number
          delivery_fee?: number
          delivery_km?: number | null
          delivery_photo?: string | null
          discount?: number
          done_at?: string | null
          driver_id?: string | null
          driver_name?: string | null
          driver_payout?: number
          fee_waived?: number
          group_id?: string | null
          hh_discount?: number
          hh_pct?: number
          id?: never
          is_gift?: boolean
          lat?: number | null
          leave_at_door?: boolean
          lng?: number | null
          loyalty_done_at?: string | null
          payment?: string | null
          points_earned?: number
          points_returned_at?: string | null
          points_used?: number
          points_value?: number
          prep_time?: number
          promo_code?: string | null
          promo_discount?: number
          scheduled_for?: string | null
          status?: Database["public"]["Enums"]["order_status"]
          store_id: string
          substitution?: string
          subtotal?: number
          tip?: number
          total?: number
          wallet_returned_at?: string | null
          wallet_used?: number
        }
        Update: {
          address?: string | null
          arrived_cust_at?: string | null
          arrived_store_at?: string | null
          cancel_note?: string | null
          cancel_reason?: string | null
          cancelled_by?: string | null
          cash_collected?: number | null
          cash_note?: string | null
          cash_settled_at?: string | null
          cashback?: number
          client_key?: string | null
          commission?: number
          commission_pct?: number
          created_at?: string
          customer_id?: string
          customer_name?: string | null
          customer_phone?: string | null
          delivery_base?: number | null
          delivery_extra?: number
          delivery_fee?: number
          delivery_km?: number | null
          delivery_photo?: string | null
          discount?: number
          done_at?: string | null
          driver_id?: string | null
          driver_name?: string | null
          driver_payout?: number
          fee_waived?: number
          group_id?: string | null
          hh_discount?: number
          hh_pct?: number
          id?: never
          is_gift?: boolean
          lat?: number | null
          leave_at_door?: boolean
          lng?: number | null
          loyalty_done_at?: string | null
          payment?: string | null
          points_earned?: number
          points_returned_at?: string | null
          points_used?: number
          points_value?: number
          prep_time?: number
          promo_code?: string | null
          promo_discount?: number
          scheduled_for?: string | null
          status?: Database["public"]["Enums"]["order_status"]
          store_id?: string
          substitution?: string
          subtotal?: number
          tip?: number
          total?: number
          wallet_returned_at?: string | null
          wallet_used?: number
        }
        Relationships: [
          {
            foreignKeyName: "orders_customer_id_fkey"
            columns: ["customer_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "orders_driver_id_fkey"
            columns: ["driver_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "orders_group_id_fkey"
            columns: ["group_id"]
            isOneToOne: false
            referencedRelation: "group_orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "orders_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          accept_blocked: boolean
          banned_at: string | null
          banned_reason: string | null
          cash_limit: number
          created_at: string
          driver_status: string | null
          id: string
          lang: string | null
          last_seen: string | null
          lat: number | null
          lng: number | null
          loc_acc: number | null
          loc_updated: string | null
          name: string | null
          online: boolean
          phone: string | null
          phone_changed_at: string | null
          role: Database["public"]["Enums"]["user_role"]
        }
        Insert: {
          accept_blocked?: boolean
          banned_at?: string | null
          banned_reason?: string | null
          cash_limit?: number
          created_at?: string
          driver_status?: string | null
          id: string
          lang?: string | null
          last_seen?: string | null
          lat?: number | null
          lng?: number | null
          loc_acc?: number | null
          loc_updated?: string | null
          name?: string | null
          online?: boolean
          phone?: string | null
          phone_changed_at?: string | null
          role?: Database["public"]["Enums"]["user_role"]
        }
        Update: {
          accept_blocked?: boolean
          banned_at?: string | null
          banned_reason?: string | null
          cash_limit?: number
          created_at?: string
          driver_status?: string | null
          id?: string
          lang?: string | null
          last_seen?: string | null
          lat?: number | null
          lng?: number | null
          loc_acc?: number | null
          loc_updated?: string | null
          name?: string | null
          online?: boolean
          phone?: string | null
          phone_changed_at?: string | null
          role?: Database["public"]["Enums"]["user_role"]
        }
        Relationships: []
      }
      promo_attempts: {
        Row: {
          at: string
          code: string | null
          ok: boolean
          user_id: string
        }
        Insert: {
          at?: string
          code?: string | null
          ok?: boolean
          user_id: string
        }
        Update: {
          at?: string
          code?: string | null
          ok?: boolean
          user_id?: string
        }
        Relationships: []
      }
      promo_codes: {
        Row: {
          code: string
          created_at: string
          ends_at: string | null
          id: string
          is_active: boolean
          kind: string
          max_uses: number | null
          min_order: number
          starts_at: string | null
          value: number
        }
        Insert: {
          code: string
          created_at?: string
          ends_at?: string | null
          id?: string
          is_active?: boolean
          kind: string
          max_uses?: number | null
          min_order?: number
          starts_at?: string | null
          value: number
        }
        Update: {
          code?: string
          created_at?: string
          ends_at?: string | null
          id?: string
          is_active?: boolean
          kind?: string
          max_uses?: number | null
          min_order?: number
          starts_at?: string | null
          value?: number
        }
        Relationships: []
      }
      promo_guess: {
        Row: {
          at: string
          bad: boolean
          id: number
          user_id: string
        }
        Insert: {
          at?: string
          bad: boolean
          id?: never
          user_id: string
        }
        Update: {
          at?: string
          bad?: boolean
          id?: never
          user_id?: string
        }
        Relationships: []
      }
      ratings: {
        Row: {
          comment: string | null
          created_at: string
          customer_id: string
          driver_id: string | null
          driver_stars: number | null
          handled_at: string | null
          handled_by: string | null
          handled_note: string | null
          order_id: number
          store_id: string
          store_stars: number | null
        }
        Insert: {
          comment?: string | null
          created_at?: string
          customer_id: string
          driver_id?: string | null
          driver_stars?: number | null
          handled_at?: string | null
          handled_by?: string | null
          handled_note?: string | null
          order_id: number
          store_id: string
          store_stars?: number | null
        }
        Update: {
          comment?: string | null
          created_at?: string
          customer_id?: string
          driver_id?: string | null
          driver_stars?: number | null
          handled_at?: string | null
          handled_by?: string | null
          handled_note?: string | null
          order_id?: number
          store_id?: string
          store_stars?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "ratings_customer_id_fkey"
            columns: ["customer_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ratings_driver_id_fkey"
            columns: ["driver_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ratings_handled_by_fkey"
            columns: ["handled_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ratings_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: true
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ratings_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
        ]
      }
      staff_members: {
        Row: {
          active: boolean
          created_at: string
          created_by: string | null
          perms: string[]
          user_id: string
        }
        Insert: {
          active?: boolean
          created_at?: string
          created_by?: string | null
          perms?: string[]
          user_id: string
        }
        Update: {
          active?: boolean
          created_at?: string
          created_by?: string | null
          perms?: string[]
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "staff_members_created_by_fkey"
            columns: ["created_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "staff_members_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: true
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      store_requests: {
        Row: {
          address: string | null
          admin_note: string | null
          category: string
          created_at: string
          decided_at: string | null
          decided_by: string | null
          id: string
          lat: number
          lng: number
          name: string
          note: string | null
          phone: string
          status: string
          store_id: string | null
          user_id: string
        }
        Insert: {
          address?: string | null
          admin_note?: string | null
          category: string
          created_at?: string
          decided_at?: string | null
          decided_by?: string | null
          id?: string
          lat: number
          lng: number
          name: string
          note?: string | null
          phone: string
          status?: string
          store_id?: string | null
          user_id: string
        }
        Update: {
          address?: string | null
          admin_note?: string | null
          category?: string
          created_at?: string
          decided_at?: string | null
          decided_by?: string | null
          id?: string
          lat?: number
          lng?: number
          name?: string
          note?: string | null
          phone?: string
          status?: string
          store_id?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "store_requests_decided_by_fkey"
            columns: ["decided_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "store_requests_store_id_fkey"
            columns: ["store_id"]
            isOneToOne: false
            referencedRelation: "stores"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "store_requests_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      stores: {
        Row: {
          address: string | null
          app_rating: number | null
          app_rating_count: number
          branch_name: string | null
          brand_id: string | null
          cashback_pct: number | null
          category: string
          commission_pct: number
          cover_url: string | null
          created_at: string
          description: string | null
          discount_pct: number
          earn_per_tjs: number | null
          fee_base: number
          fee_free_km: number
          fee_per_km: number
          fee_type: string
          free_delivery_min: number
          free_first_delivery: boolean
          google_place_id: string | null
          id: string
          is_active: boolean
          is_featured: boolean
          is_open: boolean
          lat: number | null
          lng: number | null
          logo_url: string | null
          max_discount_pct: number
          name: string
          owner_id: string | null
          phone: string | null
          points_min_order: number | null
          rating: number | null
          rating_count: number | null
          rating_updated_at: string | null
        }
        Insert: {
          address?: string | null
          app_rating?: number | null
          app_rating_count?: number
          branch_name?: string | null
          brand_id?: string | null
          cashback_pct?: number | null
          category: string
          commission_pct?: number
          cover_url?: string | null
          created_at?: string
          description?: string | null
          discount_pct?: number
          earn_per_tjs?: number | null
          fee_base?: number
          fee_free_km?: number
          fee_per_km?: number
          fee_type?: string
          free_delivery_min?: number
          free_first_delivery?: boolean
          google_place_id?: string | null
          id?: string
          is_active?: boolean
          is_featured?: boolean
          is_open?: boolean
          lat?: number | null
          lng?: number | null
          logo_url?: string | null
          max_discount_pct?: number
          name: string
          owner_id?: string | null
          phone?: string | null
          points_min_order?: number | null
          rating?: number | null
          rating_count?: number | null
          rating_updated_at?: string | null
        }
        Update: {
          address?: string | null
          app_rating?: number | null
          app_rating_count?: number
          branch_name?: string | null
          brand_id?: string | null
          cashback_pct?: number | null
          category?: string
          commission_pct?: number
          cover_url?: string | null
          created_at?: string
          description?: string | null
          discount_pct?: number
          earn_per_tjs?: number | null
          fee_base?: number
          fee_free_km?: number
          fee_per_km?: number
          fee_type?: string
          free_delivery_min?: number
          free_first_delivery?: boolean
          google_place_id?: string | null
          id?: string
          is_active?: boolean
          is_featured?: boolean
          is_open?: boolean
          lat?: number | null
          lng?: number | null
          logo_url?: string | null
          max_discount_pct?: number
          name?: string
          owner_id?: string | null
          phone?: string | null
          points_min_order?: number | null
          rating?: number | null
          rating_count?: number | null
          rating_updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "stores_brand_id_fkey"
            columns: ["brand_id"]
            isOneToOne: false
            referencedRelation: "brands"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "stores_owner_id_fkey"
            columns: ["owner_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
      support_tickets: {
        Row: {
          admin_note: string | null
          closed_at: string | null
          created_at: string
          customer_id: string
          customer_seen_at: string | null
          handled_by: string | null
          id: number
          last_customer_at: string
          last_staff_at: string | null
          order_id: number | null
          reason: string
          refund_amount: number | null
          status: string
          updated_at: string
        }
        Insert: {
          admin_note?: string | null
          closed_at?: string | null
          created_at?: string
          customer_id: string
          customer_seen_at?: string | null
          handled_by?: string | null
          id?: never
          last_customer_at?: string
          last_staff_at?: string | null
          order_id?: number | null
          reason: string
          refund_amount?: number | null
          status?: string
          updated_at?: string
        }
        Update: {
          admin_note?: string | null
          closed_at?: string | null
          created_at?: string
          customer_id?: string
          customer_seen_at?: string | null
          handled_by?: string | null
          id?: never
          last_customer_at?: string
          last_staff_at?: string | null
          order_id?: number | null
          reason?: string
          refund_amount?: number | null
          status?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "support_tickets_customer_id_fkey"
            columns: ["customer_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "support_tickets_handled_by_fkey"
            columns: ["handled_by"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "support_tickets_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
        ]
      }
      ticket_messages: {
        Row: {
          body: string
          created_at: string
          from_staff: boolean
          id: number
          sender_id: string
          ticket_id: number
        }
        Insert: {
          body: string
          created_at?: string
          from_staff?: boolean
          id?: never
          sender_id: string
          ticket_id: number
        }
        Update: {
          body?: string
          created_at?: string
          from_staff?: boolean
          id?: never
          sender_id?: string
          ticket_id?: number
        }
        Relationships: [
          {
            foreignKeyName: "ticket_messages_sender_id_fkey"
            columns: ["sender_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "ticket_messages_ticket_id_fkey"
            columns: ["ticket_id"]
            isOneToOne: false
            referencedRelation: "support_tickets"
            referencedColumns: ["id"]
          },
        ]
      }
      wallet_entries: {
        Row: {
          amount: number
          created_at: string
          created_by: string | null
          id: number
          kind: string
          note: string | null
          order_id: number | null
          ticket_id: number | null
          user_id: string
        }
        Insert: {
          amount: number
          created_at?: string
          created_by?: string | null
          id?: never
          kind: string
          note?: string | null
          order_id?: number | null
          ticket_id?: number | null
          user_id: string
        }
        Update: {
          amount?: number
          created_at?: string
          created_by?: string | null
          id?: never
          kind?: string
          note?: string | null
          order_id?: number | null
          ticket_id?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "wallet_entries_order_id_fkey"
            columns: ["order_id"]
            isOneToOne: false
            referencedRelation: "orders"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "wallet_entries_ticket_id_fkey"
            columns: ["ticket_id"]
            isOneToOne: false
            referencedRelation: "support_tickets"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "wallet_entries_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      active_contacts: {
        Args: never
        Returns: {
          customer_phone: string
          driver_phone: string
          order_id: number
        }[]
      }
      admin_assign_driver: {
        Args: { p_driver: string; p_order: number }
        Returns: undefined
      }
      admin_customers: {
        Args: { p_limit?: number; p_offset?: number; p_q?: string }
        Returns: {
          banned_at: string
          banned_reason: string
          created_at: string
          email: string
          id: string
          last_order_at: string
          name: string
          orders_count: number
          phone: string
          total_spent: number
        }[]
      }
      admin_set_customer_phone: {
        Args: { p_phone: string; p_reason: string; p_user: string }
        Returns: undefined
      }
      apply_as_driver: { Args: never; Returns: undefined }
      assign_owner: {
        Args: { p_email: string; p_store: string }
        Returns: undefined
      }
      best_dishes: {
        Args: { p_limit?: number; p_store?: string }
        Returns: {
          cnt: number
          item_id: string
          store_id: string
        }[]
      }
      branch_create: {
        Args: {
          p_address: string
          p_branch: string
          p_brand: string
          p_lat: number
          p_lng: number
          p_phone: string
        }
        Returns: string
      }
      brand_attach: {
        Args: { p_branch?: string; p_brand: string; p_store: string }
        Returns: undefined
      }
      brand_create: {
        Args: { p_name: string; p_owner_email: string }
        Returns: string
      }
      brand_detach: { Args: { p_store: string }; Returns: undefined }
      brand_route: {
        Args: {
          p_brand: string
          p_lat: number
          p_lng: number
          p_names?: string[]
        }
        Returns: {
          branch_name: string
          dist_km: number
          is_open: boolean
          missing: string[]
          name: string
          store_id: string
        }[]
      }
      brand_stats: {
        Args: { p_brand: string; p_days?: number }
        Returns: {
          branch_name: string
          cancelled: number
          delivered: number
          name: string
          orders: number
          revenue: number
          store_id: string
        }[]
      }
      brand_sync_menu: { Args: { p_from: string; p_to: string }; Returns: Json }
      can_see_order: { Args: { o: number }; Returns: boolean }
      cash_balances: {
        Args: never
        Returns: {
          balance: number
          driver_id: string
        }[]
      }
      check_image_url: { Args: { u: string }; Returns: boolean }
      check_promo: {
        Args: { p_code: string; p_items: Json; p_store: string }
        Returns: Json
      }
      check_promo_base: {
        Args: { p_code: string; p_items: Json; p_store: string }
        Returns: Json
      }
      contacts_for: {
        Args: { p_ids: number[] }
        Returns: {
          customer_phone: string
          driver_phone: string
          order_id: number
        }[]
      }
      copy_menu: {
        Args: { p_from: string; p_to: string; p_update: boolean }
        Returns: Json
      }
      courier_steps_version: { Args: never; Returns: number }
      create_ticket: {
        Args: { p_message: string; p_order: number; p_reason: string }
        Returns: number
      }
      decide_store_request: {
        Args: { p_approve: boolean; p_id: string; p_note?: string }
        Returns: string
      }
      deliver_order: {
        Args: {
          p_cash?: number
          p_id: number
          p_note?: string
          p_photo?: string
        }
        Returns: undefined
      }
      delivery_calc: {
        Args: { p_lat: number; p_lng: number; p_store: string; p_uid: string }
        Returns: Json
      }
      delivery_quote: {
        Args: { p_lat: number; p_lng: number; p_store: string }
        Returns: Json
      }
      dispatch_next: { Args: { p_order: number }; Returns: undefined }
      dispatch_tick: { Args: never; Returns: undefined }
      dist_km: {
        Args: { a1: number; a2: number; o1: number; o2: number }
        Returns: number
      }
      driver_accept: { Args: { p_id: number }; Returns: boolean }
      driver_arrived: {
        Args: { p_id: number; p_where: string }
        Returns: undefined
      }
      driver_decline: { Args: { p_id: number }; Returns: undefined }
      driver_location: {
        Args: { p_acc?: number; p_lat: number; p_lng: number }
        Returns: undefined
      }
      driver_ping: { Args: { p_online: boolean }; Returns: undefined }
      eligible_couriers: {
        Args: { p_order: number; p_reoffer?: boolean }
        Returns: {
          dist: number
          fresh: boolean
          id: string
        }[]
      }
      group_add: {
        Args: {
          p_id: string
          p_item: string
          p_note?: string
          p_options?: Json
          p_qty: number
        }
        Returns: Json
      }
      group_create: { Args: { p_store: string }; Returns: Json }
      group_get: { Args: { p_id: string }; Returns: Json }
      group_json: { Args: { p_id: string }; Returns: Json }
      group_remove: { Args: { p_line: number }; Returns: Json }
      group_set: { Args: { p_id: string; p_status: string }; Returns: Json }
      happy_hour_pct: {
        Args: { p_at?: string; p_store: string }
        Returns: number
      }
      has_perm: { Args: { p: string }; Returns: boolean }
      is_admin: { Args: never; Returns: boolean }
      loyalty_balance: { Args: { p_user: string }; Returns: number }
      loyalty_setting: { Args: { p_key: string }; Returns: number }
      loyalty_spend: {
        Args: { p_order: number; p_points: number; p_user: string }
        Returns: undefined
      }
      loyalty_summary: { Args: never; Returns: Json }
      my_offers: {
        Args: never
        Returns: {
          dist_km: number
          mode: string
          order_id: number
          rank: number
          secs_left: number
        }[]
      }
      my_perms: { Args: never; Returns: string[] }
      my_rating: { Args: never; Returns: Json }
      norm_phone: { Args: { p: string }; Returns: string }
      order_contacts: { Args: { p_order: number }; Returns: Json }
      order_courier_position: {
        Args: { p_order: number }
        Returns: {
          acc: number
          lat: number
          lng: number
          updated_at: string
        }[]
      }
      owns_store: { Args: { s: string }; Returns: boolean }
      place_order: {
        Args: {
          p_address?: string
          p_extra?: Json
          p_fee?: number
          p_items: Json
          p_key?: string
          p_lat?: number
          p_lng?: number
          p_payment?: string
          p_points?: number
          p_promo?: string
          p_store: string
          p_tip?: number
          p_wallet?: number
        }
        Returns: number
      }
      price_line: { Args: { p_item: string; p_opts: Json }; Returns: Json }
      promo_eval: {
        Args: {
          p_base: number
          p_code: string
          p_gate?: number
          p_lock?: boolean
          p_uid: string
        }
        Returns: number
      }
      promo_guard_version: { Args: never; Returns: number }
      rate_order: {
        Args: {
          p_comment?: string
          p_driver: number
          p_order: number
          p_store: number
        }
        Returns: undefined
      }
      reject_order: {
        Args: { p_id: number; p_note?: string; p_reason: string }
        Returns: undefined
      }
      reopen_rating: { Args: { p_order: number }; Returns: undefined }
      report_client_error: {
        Args: {
          p_app: string
          p_context?: string
          p_message: string
          p_ua?: string
        }
        Returns: undefined
      }
      request_store: {
        Args: {
          p_address: string
          p_category: string
          p_lat: number
          p_lng: number
          p_name: string
          p_note?: string
          p_phone: string
        }
        Returns: string
      }
      resolve_rating: {
        Args: { p_note?: string; p_order: number }
        Returns: undefined
      }
      set_customer_ban: {
        Args: { p_banned: boolean; p_id: string; p_reason?: string }
        Returns: undefined
      }
      set_default_address: { Args: { p_id: string }; Returns: undefined }
      set_my_cashback: {
        Args: { p_pct: number; p_store: string }
        Returns: undefined
      }
      set_my_discount: {
        Args: { p_pct: number; p_store: string }
        Returns: undefined
      }
      set_my_free_delivery: {
        Args: { p_min: number; p_store: string }
        Returns: undefined
      }
      set_my_phone: { Args: { p_phone: string }; Returns: undefined }
      set_order_status: {
        Args: {
          p_id: number
          p_to: Database["public"]["Enums"]["order_status"]
        }
        Returns: undefined
      }
      set_page: {
        Args: { p_body: string; p_lang: string; p_slug: string }
        Returns: undefined
      }
      set_prep_time: {
        Args: { p_id: number; p_min: number }
        Returns: undefined
      }
      set_setting: {
        Args: { p_key: string; p_value: number }
        Returns: undefined
      }
      set_store_earn: {
        Args: { p_earn: number; p_store: string }
        Returns: undefined
      }
      set_store_free_delivery: {
        Args: { p_min: number; p_store: string }
        Returns: undefined
      }
      set_store_loyalty: {
        Args: { p_cashback: number; p_min_order: number; p_store: string }
        Returns: undefined
      }
      set_store_open: {
        Args: { p_open: boolean; p_store: string }
        Returns: undefined
      }
      set_text_setting: {
        Args: { p_key: string; p_value: string }
        Returns: undefined
      }
      settle_driver_cash: { Args: { p_driver: string }; Returns: number }
      staff_list: {
        Args: never
        Returns: {
          active: boolean
          created_at: string
          email: string
          name: string
          perms: string[]
          user_id: string
        }[]
      }
      staff_remove: { Args: { p_user: string }; Returns: undefined }
      staff_set: {
        Args: { p_active?: boolean; p_email: string; p_perms: string[] }
        Returns: undefined
      }
      store_owner_info: {
        Args: { p_store: string }
        Returns: {
          email: string
          name: string
          owner_id: string
        }[]
      }
      store_private: {
        Args: never
        Returns: {
          commission_pct: number
          id: string
          max_discount_pct: number
          owner_id: string
        }[]
      }
      store_speed: {
        Args: never
        Returns: {
          avg_min: number
          n: number
          store_id: string
        }[]
      }
      ticket_reason_ok: {
        Args: { p_has_order: boolean; p_reason: string; p_status: string }
        Returns: boolean
      }
      ticket_refund_room: {
        Args: { p_ticket: number }
        Returns: {
          order_total: number
          refunded: number
          room: number
        }[]
      }
      ticket_reply: {
        Args: { p_body: string; p_ticket: number }
        Returns: undefined
      }
      ticket_seen: { Args: { p_ticket: number }; Returns: undefined }
      ticket_set_status: {
        Args: {
          p_note?: string
          p_refund?: number
          p_status: string
          p_ticket: number
        }
        Returns: undefined
      }
      ticket_staff_reply: {
        Args: { p_body: string; p_ticket: number }
        Returns: undefined
      }
      update_my_store: {
        Args: {
          p_cover: string
          p_description: string
          p_logo?: string
          p_store: string
        }
        Returns: undefined
      }
      wallet_adjust: {
        Args: { p_amount: number; p_note: string; p_user: string }
        Returns: undefined
      }
      wallet_balance: { Args: { p_user?: string }; Returns: number }
    }
    Enums: {
      order_status:
        | "pending"
        | "preparing"
        | "ready"
        | "pickedup"
        | "delivered"
        | "rejected"
        | "cancelled"
      user_role: "customer" | "merchant" | "driver" | "admin"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends (DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never) = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends (DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never) = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends (PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never) = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      order_status: [
        "pending",
        "preparing",
        "ready",
        "pickedup",
        "delivered",
        "rejected",
        "cancelled",
      ],
      user_role: ["customer", "merchant", "driver", "admin"],
    },
  },
} as const

