/**
 * Xử lý màu sắc và định dạng KPI theo Hợp đồng API N4.6
 */

export const COLORS = {
  good: '#10b981',      // Xanh lá - Tốt
  medium: '#f59e0b',    // Vàng cam - Trung bình
  poor: '#ef4444',      // Đỏ - Kém
  missing: '#9ca3af',   // Xám - Không có dữ liệu
  noTraffic: '#64748b', // Xám xanh - Không có lưu lượng
  defaultBorder: '#334155',
  partialBorder: '#d97706',
  highlight: '#2563eb',
}

/**
 * Tính toán mức chất lượng fallback khi backend chưa trả quality_level
 */
export function deriveQualityLevel(kpiCode, value) {
  if (value === null || value === undefined) return null

  switch (kpiCode) {
    case 'cssr': // Càng cao càng tốt (%), QCVN: >=98 tốt, >=95 trung bình, <95 kém
      if (value >= 98) return 'good'
      if (value >= 95) return 'medium'
      return 'poor'

    case 'service_drop_all': // Càng thấp càng tốt (%), QCVN: <=2 tốt, <=5 trung bình, >5 kém
      if (value <= 2) return 'good'
      if (value <= 5) return 'medium'
      return 'poor'

    case 'user_throughput': // Càng cao càng tốt (Mbps), VNPT: >=16 tốt, >=5 trung bình, <5 kém
      if (value >= 16) return 'good'
      if (value >= 5) return 'medium'
      return 'poor'

    default:
      return null
  }
}

/**
 * Lấy màu tô fillColor dựa trên item KPI và cấu hình KPI
 */
export function getKpiFillColor(item, kpiMeta, maxTraffic = 500) {
  if (!item) return COLORS.missing

  // 1. Kiểm tra không có traffic
  if (item.reason === 'no_positive_traffic') {
    return COLORS.noTraffic
  }

  // 2. Kiểm tra missing hoặc value null
  if (item.status === 'missing' || item.value === null || item.value === undefined) {
    return COLORS.missing
  }

  // 3. Nếu là traffic (không có ngưỡng, tô theo thang liên tục)
  if (kpiMeta?.kpi_code === 'traffic') {
    const v = item.value
    // Thang màu từ xanh dương nhạt đến tím đậm
    if (v <= 0) return COLORS.noTraffic
    const ratio = Math.min(Math.max(v / (maxTraffic || 100), 0.1), 1)
    if (ratio < 0.25) return '#93c5fd'
    if (ratio < 0.5) return '#60a5fa'
    if (ratio < 0.75) return '#3b82f6'
    return '#1d4ed8'
  }

  // 4. Lấy quality_level từ API hoặc từ hàm tính fallback
  const qLevel = item.quality_level || deriveQualityLevel(kpiMeta?.kpi_code, item.value)

  if (qLevel === 'good') return COLORS.good
  if (qLevel === 'medium') return COLORS.medium
  if (qLevel === 'poor') return COLORS.poor

  return '#94a3b8'
}

/**
 * Lấy style đường viền Leaflet (đặc biệt cho status: 'partial')
 */
export function getKpiStrokeStyle(item) {
  if (!item) {
    return {
      color: COLORS.defaultBorder,
      weight: 1,
      dashArray: null,
    }
  }

  // Thiếu một phần cell -> vẽ viền nét đứt màu cam đậm để dễ nhận biết
  if (item.status === 'partial') {
    return {
      color: COLORS.partialBorder,
      weight: 2.5,
      dashArray: '5, 5',
    }
  }

  return {
    color: COLORS.defaultBorder,
    weight: 1.2,
    dashArray: null,
  }
}

/**
 * Định dạng hiển thị giá trị KPI thân thiện
 */
export function formatKpiDisplay(item, kpiMeta) {
  if (!item) return 'Không có dữ liệu'

  if (item.reason === 'no_positive_traffic') {
    return 'Không có lưu lượng (traffic = 0)'
  }

  if (item.status === 'missing' || item.value === null || item.value === undefined) {
    return 'Không có dữ liệu'
  }

  const unit = kpiMeta?.unit ? ` ${kpiMeta.unit}` : ''
  const valStr = typeof item.value === 'number' ? item.value.toFixed(2) : item.value
  return `${valStr}${unit}`
}

/**
 * Nhãn trạng thái hiển thị
 */
export function getStatusBadge(item) {
  if (!item) return { label: 'Chưa có dữ liệu', color: '#6b7280' }

  if (item.reason === 'no_positive_traffic') {
    return { label: 'Không có lưu lượng', color: COLORS.noTraffic }
  }

  if (item.status === 'missing' || item.value === null) {
    return { label: 'Mất tín hiệu / Thiếu dữ liệu', color: COLORS.missing }
  }

  if (item.status === 'partial') {
    const reported = item.cells_reported ?? item.cell_hours_reported ?? '?'
    const total = item.cells_total ?? item.cell_hours_expected ?? '?'
    return {
      label: `Dữ liệu một phần (${reported}/${total} cell)`,
      color: COLORS.partialBorder,
    }
  }

  return { label: 'Đầy đủ (OK)', color: COLORS.good }
}

/**
 * Tên mức chất lượng hiển thị
 */
export function getQualityLevelName(item, kpiMeta) {
  if (item?.value === null || item?.value === undefined) return 'N/A'
  if (kpiMeta?.kpi_code === 'traffic') return 'Lưu lượng tổng'

  const q = item.quality_level || deriveQualityLevel(kpiMeta?.kpi_code, item.value)
  if (q === 'good') return 'Tốt'
  if (q === 'medium') return 'Trung bình'
  if (q === 'poor') return 'Kém'
  return 'Chưa phân loại'
}
