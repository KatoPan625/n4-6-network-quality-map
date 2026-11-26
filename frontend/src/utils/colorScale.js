/**
 * Xử lý màu sắc và định dạng KPI theo Hợp đồng API N4.6
 * Áp dụng trực tiếp quality_level (good, medium, poor) từ API
 * Không dùng ngưỡng hardcode ở Frontend
 */

export const COLORS = {
  good: '#10b981',       // Xanh lá - Tốt
  medium: '#f59e0b',     // Vàng cam - Trung bình
  poor: '#ef4444',       // Đỏ - Kém
  missing: '#9ca3af',    // Xám - Không có dữ liệu
  noTraffic: '#64748b',  // Xám xanh - Không có lưu lượng (traffic = 0)
  nonQuality: '#38bdf8', // Xanh dương trung tính cho KPI không phân loại chất lượng
  unclassified: '#94a3b8', // Xám trung tính khi quality_level là null
  defaultBorder: '#334155',
  partialBorder: '#d97706',
  highlight: '#2563eb',
}

/**
 * Kiểm tra KPI có phải KPI chất lượng (dùng cờ is_quality_kpi từ /api/v1/kpis)
 */
export function isQualityKpi(kpiMeta) {
  if (!kpiMeta) return false
  if (typeof kpiMeta.is_quality_kpi === 'boolean') {
    return kpiMeta.is_quality_kpi
  }
  return kpiMeta.higher_is_better !== null && kpiMeta.higher_is_better !== undefined
}

/**
 * Lấy màu tô fillColor dựa trên item KPI và cấu hình KPI
 * Hoàn toàn dựa trên quality_level từ API trả về, không dùng ngưỡng fallback
 */
export function getKpiFillColor(item, kpiMeta) {
  if (!item) return COLORS.missing

  // 1. Kiểm tra trường hợp không có lưu lượng (reason = 'no_positive_traffic')
  if (item.reason === 'no_positive_traffic') {
    return COLORS.noTraffic
  }

  // 2. Kiểm tra missing hoặc value null -> Tô màu xám theo trạng thái
  if (item.status === 'missing' || item.value === null || item.value === undefined) {
    return COLORS.missing
  }

  // 3. Nếu không phải KPI chất lượng (is_quality_kpi === false): tô màu đơn sắc trung tính
  if (!isQualityKpi(kpiMeta)) {
    return COLORS.nonQuality
  }

  // 4. Với các KPI chất lượng: Sử dụng trực tiếp quality_level từ API
  if (item.quality_level === 'good') return COLORS.good
  if (item.quality_level === 'medium') return COLORS.medium
  if (item.quality_level === 'poor') return COLORS.poor

  // 5. Nếu quality_level là null (chưa có ngưỡng): Tô màu trung tính
  return COLORS.unclassified
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
 * Tên mức chất lượng hiển thị (chỉ đọc trực tiếp từ API)
 */
export function getQualityLevelName(item, kpiMeta) {
  if (item?.value === null || item?.value === undefined) return 'N/A'

  // KPI không phải chất lượng (is_quality_kpi === false) thì không phân loại chất lượng
  if (!isQualityKpi(kpiMeta)) return null

  if (item.quality_level === 'good') return 'Tốt'
  if (item.quality_level === 'medium') return 'Trung bình'
  if (item.quality_level === 'poor') return 'Kém'

  return 'Chưa có ngưỡng đánh giá'
}
