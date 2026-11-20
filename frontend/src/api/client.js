/**
 * API Client kết nối tới Backend FastAPI của N4.6
 * Hỗ trợ CORS / Proxy tại localhost:5173 -> localhost:8000
 */

const BASE_URL = '' // Proxy của Vite tự chuyển /api sang http://localhost:8000

export async function fetchKpis() {
  const res = await fetch(`${BASE_URL}/api/v1/kpis`)
  if (!res.ok) throw new Error(`Lỗi tải danh mục KPI: ${res.statusText}`)
  return res.json()
}

export async function fetchSources() {
  const res = await fetch(`${BASE_URL}/api/v1/sources`)
  if (!res.ok) throw new Error(`Lỗi tải danh sách nguồn dữ liệu: ${res.statusText}`)
  return res.json()
}

// Caching trong bộ nhớ để không tải lại ranh giới mỗi lần đổi bộ lọc
const regionsCache = new Map()

export async function fetchRegions(level = 'province', simplify = 0.001) {
  const cacheKey = `${level}_${simplify}`
  if (regionsCache.has(cacheKey)) {
    return regionsCache.get(cacheKey)
  }

  const res = await fetch(`${BASE_URL}/api/v1/regions?level=${level}&simplify=${simplify}`)
  if (!res.ok) throw new Error(`Lỗi tải ranh giới ${level}: ${res.statusText}`)
  const data = await res.json()
  regionsCache.set(cacheKey, data)
  return data
}

export async function fetchKpiValues({
  kpi = 'cssr',
  at = '2026-10-02T10:00',
  level = 'province',
  periodType = 'hour',
  source = 'BE-SAMPLE',
}) {
  const params = new URLSearchParams({
    kpi,
    at,
    level,
    period_type: periodType,
    source,
  })

  const res = await fetch(`${BASE_URL}/api/v1/kpi-values?${params.toString()}`)
  if (!res.ok) {
    const errorBody = await res.text()
    throw new Error(`Lỗi tải số liệu KPI (${res.status}): ${errorBody}`)
  }
  return res.json()
}

export async function fetchRegionKpis({
  regionCode,
  kpi = null,
  periodType = 'hour',
  source = 'BE-SAMPLE',
  from = null,
  to = null,
}) {
  const params = new URLSearchParams({
    period_type: periodType,
    source,
  })
  if (kpi) params.append('kpi', kpi)
  if (from) params.append('from', from)
  if (to) params.append('to', to)

  const res = await fetch(`${BASE_URL}/api/v1/regions/${regionCode}/kpis?${params.toString()}`)
  if (!res.ok) {
    const errorBody = await res.text()
    throw new Error(`Lỗi tải chuỗi thời gian vùng ${regionCode} (${res.status}): ${errorBody}`)
  }
  return res.json()
}
