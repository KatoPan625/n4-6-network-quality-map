import React from 'react'

export default function FilterBar({
  kpis,
  selectedKpi,
  onSelectKpi,
  level,
  onChangeLevel,
  periodType,
  onChangePeriodType,
  at,
  onChangeAt,
  sources,
  selectedSource,
  onChangeSource,
  loading,
}) {
  // Tạo danh sách các giờ mẫu nhanh cho BE-SAMPLE (01/10/2026 đến 03/10/2026)
  const isSample = selectedSource === 'BE-SAMPLE'

  // Điều hướng thời gian tới/lùi 1 bước
  const handleStepTime = (delta) => {
    if (periodType === 'day') {
      const currentDate = new Date(at)
      currentDate.setDate(currentDate.getDate() + delta)
      const y = currentDate.getFullYear()
      const m = String(currentDate.getMonth() + 1).padStart(2, '0')
      const d = String(currentDate.getDate()).padStart(2, '0')
      onChangeAt(`${y}-${m}-${d}`)
    } else {
      const currentDate = new Date(at)
      currentDate.setHours(currentDate.getHours() + delta)
      const y = currentDate.getFullYear()
      const m = String(currentDate.getMonth() + 1).padStart(2, '0')
      const d = String(currentDate.getDate()).padStart(2, '0')
      const h = String(currentDate.getHours()).padStart(2, '0')
      onChangeAt(`${y}-${m}-${d}T${h}:00`)
    }
  }

  return (
    <header className="filter-bar">
      <div className="filter-brand">
        <h1 className="brand-title">N4.6 Mạng 4G</h1>
        <span className="brand-subtitle">UTH – VNPT NET</span>
      </div>

      <div className="filter-controls">
        {/* Chọn Cấp hành chính */}
        <div className="filter-item">
          <label className="filter-label">Cấp xem:</label>
          <div className="pill-group">
            <button
              className={`pill-btn ${level === 'province' ? 'active' : ''}`}
              onClick={() => onChangeLevel('province')}
            >
              Tỉnh / Thành (34)
            </button>
            <button
              className={`pill-btn ${level === 'ward' ? 'active' : ''}`}
              onClick={() => onChangeLevel('ward')}
            >
              Phường / Xã (TP.HCM)
            </button>
          </div>
        </div>

        {/* Chọn KPI */}
        <div className="filter-item">
          <label className="filter-label">Chỉ số KPI:</label>
          <select
            className="filter-select kpi-select"
            value={selectedKpi}
            onChange={(e) => onSelectKpi(e.target.value)}
          >
            {kpis.map((k) => (
              <option key={k.kpi_code} value={k.kpi_code}>
                {k.kpi_name} ({k.unit})
              </option>
            ))}
          </select>
        </div>

        {/* Chọn Chu kỳ: Giờ / Ngày */}
        <div className="filter-item">
          <label className="filter-label">Chu kỳ:</label>
          <div className="pill-group">
            <button
              className={`pill-btn ${periodType === 'hour' ? 'active' : ''}`}
              onClick={() => onChangePeriodType('hour')}
            >
              Giờ
            </button>
            <button
              className={`pill-btn ${periodType === 'day' ? 'active' : ''}`}
              onClick={() => onChangePeriodType('day')}
            >
              Ngày
            </button>
          </div>
        </div>

        {/* Chọn Mốc thời gian */}
        <div className="filter-item time-item">
          <label className="filter-label">Thời điểm:</label>
          <div className="time-stepper">
            <button
              className="stepper-btn"
              onClick={() => handleStepTime(-1)}
              title="Lùi 1 mốc"
            >
              ◀
            </button>
            <input
              type={periodType === 'day' ? 'date' : 'datetime-local'}
              className="filter-input-date"
              value={periodType === 'day' ? at.substring(0, 10) : at.substring(0, 16)}
              step={periodType === 'hour' ? 3600 : undefined}
              onChange={(e) => {
                const val = e.target.value
                if (!val) return
                if (periodType === 'day') {
                  onChangeAt(val)
                } else {
                  // Đảm bảo định dạng YYYY-MM-DDTHH:00
                  const cleanHour = val.length === 16 ? `${val.substring(0, 13)}:00` : val
                  onChangeAt(cleanHour)
                }
              }}
            />
            <button
              className="stepper-btn"
              onClick={() => handleStepTime(1)}
              title="Tiến 1 mốc"
            >
              ▶
            </button>
          </div>
        </div>

        {/* Chọn Nguồn dữ liệu */}
        <div className="filter-item">
          <label className="filter-label">Nguồn:</label>
          <select
            className="filter-select"
            value={selectedSource}
            onChange={(e) => onChangeSource(e.target.value)}
          >
            {sources.map((s) => (
              <option key={s.source_code} value={s.source_code}>
                {s.source_code} {s.is_default ? '(Mặc định)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="filter-status">
        {loading && <span className="spinner-badge">Đang cập nhật...</span>}
      </div>
    </header>
  )
}
