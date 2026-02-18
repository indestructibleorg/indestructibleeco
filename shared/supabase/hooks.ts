'use client';

import { useEffect, useState } from 'react';
import { supabase } from './client';
import type { User, Database } from './types';

/**
 * Hook for getting current authenticated user
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const getUser = async () => {
      try {
        setLoading(true);
        const { data, error } = await supabase.auth.getSession();

        if (error) {
          setError(error);
          setUser(null);
          return;
        }

        if (data?.session?.user?.id) {
          const { data: userData, error: userError } = await supabase
            .from('users')
            .select('*')
            .eq('id', data.session.user.id)
            .single();

          if (userError) {
            setError(userError);
          } else {
            setUser(userData as User);
          }
        } else {
          setUser(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    getUser();

    // Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        try {
          if (session?.user?.id) {
            const { data: userData, error: userError } = await supabase
              .from('users')
              .select('*')
              .eq('id', session.user.id)
              .single();

            if (userError) {
              setError(userError);
            } else {
              setUser(userData as User);
              setError(null);
            }
          } else {
            setUser(null);
            setError(null);
          }
        } catch (err) {
          setError(err instanceof Error ? err : new Error('Unknown error'));
        }
      }
    );

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  return { user, loading, error };
}

/**
 * Hook for real-time updates to a table
 */
export function useRealtimeSubscription<T extends keyof Database['public']['Tables']>(
  table: T,
  filter?: { column: string; value: any }
) {
  const [data, setData] = useState<Database['public']['Tables'][T]['Row'][]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        let query = supabase.from(table).select('*');

        if (filter) {
          query = query.eq(filter.column, filter.value);
        }

        const { data: fetchedData, error: fetchError } = await query;

        if (fetchError) {
          setError(fetchError);
        } else {
          setData(fetchedData as Database['public']['Tables'][T]['Row'][]);
        }
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Subscribe to real-time changes
    const subscription = supabase
      .channel(`${table}_changes`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: table as string,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setData((prev) => [...prev, payload.new as Database['public']['Tables'][T]['Row']]);
          } else if (payload.eventType === 'UPDATE') {
            setData((prev) =>
              prev.map((item) =>
                (item as any).id === (payload.new as any).id
                  ? (payload.new as Database['public']['Tables'][T]['Row'])
                  : item
              )
            );
          } else if (payload.eventType === 'DELETE') {
            setData((prev) => prev.filter((item) => (item as any).id !== (payload.old as any).id));
          }
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [table, filter]);

  return { data, loading, error };
}
