import type { Centre, CentreRaw } from "@/lib/types";

export function centreFromRaw(raw: CentreRaw): Centre {
  const specialities = Array.isArray(raw.specialities)
    ? raw.specialities
    : (raw.specialities ? raw.specialities.split(",").map((s) => s.trim()).filter(Boolean) : []);

  return {
    id: raw.id,
    name: raw.name,
    level: raw.level,
    specialities,
    capacity_max: raw.capacity_max ?? 0,
    capacity_available: raw.capacity_available,
    estimated_wait_minutes: raw.estimated_wait_minutes,
    lat: raw.lat ?? null,
    lon: raw.lon ?? null,
    catchment_population: raw.catchment_population ?? 0,
  };
}

export function centreToRaw(centre: Centre): CentreRaw {
  return {
    ...centre,
    specialities: Array.isArray(centre.specialities)
      ? centre.specialities
      : [],
  };
}
