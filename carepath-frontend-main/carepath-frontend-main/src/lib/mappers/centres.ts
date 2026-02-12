import type { Centre, CentreRaw } from "@/lib/types";

export function centreFromRaw(raw: CentreRaw): Centre {
  return {
    ...raw,
    specialities: raw.specialities
      ? raw.specialities.split(",").map((s) => s.trim()).filter(Boolean)
      : [],
  };
}

export function centreToRaw(centre: Centre): CentreRaw {
  return {
    ...centre,
    specialities: centre.specialities.join(","),
  };
}
