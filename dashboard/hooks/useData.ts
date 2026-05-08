import { create } from 'zustand';
import { Match, Delivery, VenueCoord } from '@/types/cricket';
import { loadAllData } from '@/lib/data';

interface DataStore {
  matches: Match[];
  deliveries: Delivery[];
  venues: VenueCoord[];
  loading: boolean;
  error: string | null;
  loaded: boolean;
  loadData: () => Promise<void>;
}

export const useDataStore = create<DataStore>((set, get) => ({
  matches: [],
  deliveries: [],
  venues: [],
  loading: false,
  error: null,
  loaded: false,
  loadData: async () => {
    if (get().loaded || get().loading) return;
    set({ loading: true, error: null });
    try {
      const { matches, deliveries, venues } = await loadAllData();
      set({ matches, deliveries, venues, loading: false, loaded: true });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
