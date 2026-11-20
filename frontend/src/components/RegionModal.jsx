import React, { useEffect, useRef, useState } from 'react'
import Chart from 'chart.js/auto'
import { fetchRegionKpis } from '../api/client'
import { formatKpiDisplay, getStatusBadge, getQualityLevelName } from '../utils/colorScale'

export default function RegionModal({
  region,
  kpiList,
  currentKpi,
  currentPeriodType,
  currentSource,
  onClose,
}) {
  const [selectedKpi, setSelectedKpi] = useState(currentKpi)
  const [periodType, setPeriodType] = useState(currentPeriodType || 'hour')
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const canvasRef = useRef(null)
  const chartInstanceRef = useRef(null)

  const regionCode = region?.properties?.region_code
  const regionName = region?.properties?.region_name

  // Tải dữ liệu chuỗi thời gian khi đổi region, KPI hoặc periodType
  useEffect(() => {
    if (!regionCode) return

    let isMounted = true
    setLoading(true)
    setError(null)

    fetchRegionKpis({
      regionCode,
      kpi: selectedKpi,
      periodType,
      source: currentSource || 'BE-SAMPLE',
    })
      .then((data) => {
        if (!isMounted) return
        setChartData(data)
        setLoading(false)
      })
      .catch((err) => {
        if (!isMounted) return
        setError(err.message)
        setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [regionCode, selectedKpi, periodType, currentSource])

  // Vẽ biểu đồ Chart.js khi chartData thay đổi
  useEffect(() => {
    if (!canvasRef.current || !chartData || loading) return

    // Hủy instance cũ nếu đã tồn tại
    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy()
    }

    const kpiSeriesObj = chartData.kpis?.find((k) => k.kpi_code === selectedKpi) || chartData.kpis?.[0]
    if (!kpiSeriesObj) return

    const series = kpiSeriesObj.series || []
    const labels = series.map((s) => {
      // Định dạng mốc thời gian trục X
      if (periodType === 'hour') {
        const d = new Date(s.at)
        return `${d.getDate()}/${d.getMonth() + 1} ${String(d.getHours()).padStart(2, '0')}:00`
      }
      return s.at
    })

    const values = series.map((s) => (s.value !== null ? s.value : null))

    const ctx = canvasRef.current.getContext('2d')
    chartInstanceRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: `${kpiSeriesObj.kpi_name} (${kpiSeriesObj.unit})`,
            data: values,
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            fill: true,
            tension: 0.25,
            pointRadius: series.length > 30 ? 2 : 4,
            pointHoverRadius: 6,
            spanGaps: false, // Ngắt quãng nếu value là null (missing)
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const val = context.parsed.y
                const rawItem = series[context.dataIndex]
                if (val === null || val === undefined) {
                  return `Giá trị: Không có dữ liệu (status: ${rawItem?.status || 'missing'})`
                }
                let text = `Giá trị: ${val.toFixed(2)} ${kpiSeriesObj.unit}`
                if (rawItem?.status === 'partial') {
                  text += ` (Một phần: ${rawItem.cells_reported}/${rawItem.cells_total} cell)`
                }
                return text
              },
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: {
              maxRotation: 45,
              autoSkip: true,
              maxTicksLimit: 12,
            },
          },
          y: {
            beginAtZero: selectedKpi === 'traffic' || selectedKpi === 'service_drop_all',
            grid: { color: 'rgba(0, 0, 0, 0.06)' },
            title: {
              display: true,
              text: kpiSeriesObj.unit,
            },
          },
        },
      },
    })

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy()
      }
    }
  }, [chartData, selectedKpi, periodType, loading])

  const currentKpiObj = kpiList.find((k) => k.kpi_code === selectedKpi)

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title">
              {regionName} <span className="modal-code">({regionCode})</span>
            </h3>
            <div className="modal-subtitle">
              Cấp: {region?.properties?.region_level === 'province' ? 'Tỉnh / Thành phố' : 'Phường / Xã'}
              {region?.properties?.parent_code && ` (Trực thuộc: ${region.properties.parent_code})`}
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* Bộ lọc trong modal */}
        <div className="modal-controls">
          <div className="control-group">
            <label>Chọn KPI:</label>
            <select
              value={selectedKpi}
              onChange={(e) => setSelectedKpi(e.target.value)}
              className="select-input"
            >
              {kpiList.map((k) => (
                <option key={k.kpi_code} value={k.kpi_code}>
                  {k.kpi_name} ({k.unit})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Chu kỳ:</label>
            <div className="segmented-control">
              <button
                className={`seg-btn ${periodType === 'hour' ? 'active' : ''}`}
                onClick={() => setPeriodType('hour')}
              >
                Theo Giờ
              </button>
              <button
                className={`seg-btn ${periodType === 'day' ? 'active' : ''}`}
                onClick={() => setPeriodType('day')}
              >
                Theo Ngày
              </button>
            </div>
          </div>
        </div>

        {/* Khu vực vẽ đồ thị */}
        <div className="modal-body">
          {loading && <div className="chart-loading">Đang tải chuỗi dữ liệu thời gian...</div>}
          {error && <div className="chart-error">Lỗi: {error}</div>}
          <div className="chart-container" style={{ display: loading || error ? 'none' : 'block' }}>
            <canvas ref={canvasRef}></canvas>
          </div>
        </div>

        <div className="modal-footer">
          <div className="modal-info">
            * Nguồn dữ liệu: <strong>{currentSource || 'BE-SAMPLE'}</strong> (Dữ liệu mô phỏng di động 4G)
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  )
}
