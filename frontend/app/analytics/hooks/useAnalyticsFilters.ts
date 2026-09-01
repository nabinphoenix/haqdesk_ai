"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { defaultAnalyticsFilters, filtersFromSearchParams, filtersToSearchParams } from "../analytics-utils";
import type { AnalyticsFilterState } from "../types";

export function useAnalyticsFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const defaults = useMemo(() => defaultAnalyticsFilters(), []);
  const filters = useMemo(
    () => filtersFromSearchParams(new URLSearchParams(searchParams.toString()), defaults),
    [searchParams, defaults],
  );

  const replace = useCallback((next: AnalyticsFilterState) => {
    const params = filtersToSearchParams(next);
    const view = searchParams.get("view");
    if (view) params.set("view", view);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [pathname, router, searchParams]);

  const setFilter = useCallback(<K extends keyof AnalyticsFilterState>(
    key: K,
    value: AnalyticsFilterState[K],
  ) => replace({ ...filters, [key]: value }), [filters, replace]);

  const setFilters = useCallback((next: Partial<AnalyticsFilterState>) => {
    replace({ ...filters, ...next });
  }, [filters, replace]);

  const resetFilters = useCallback(() => replace(defaults), [defaults, replace]);
  const queryString = useMemo(() => filtersToSearchParams(filters).toString(), [filters]);

  return { filters, setFilter, setFilters, resetFilters, queryString };
}