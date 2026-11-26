import React, { useEffect, useRef, useState } from 'react'
import Chart from 'chart.js/auto'
import { fetchRegionKpis } from '../api/client'
import { isQualityKpi } from '../utils/colorScale'

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
  const [fetchResult, setFetchResult] = useState({ key: null, data: null, error: null })

  const canvasRef = useRef(null)
  const chartInstanceRef = useRef(null)

  const regionCode = region?.properties?.region_code
  const regionName = region?.properties?.region_name
  const sourceCode = currentSource || 'BE-SAMPLE'
  const requestKey = regionCode ? `${regionCode}|${selectedKpi}|${periodType}|${sourceCode}` : null

  const loading = Boolean(requestKey) && fetchResult.key !== requestKey
  const error = fetchResult.key === requestKey ? fetchResult.error : null
  const chartData = fetchResult.key === requestKey ? fetchResult.data : null

  const currentKpiObj = kpiList.find((k) => k.kpi_code === selectedKpi)

  // Tải dữ liệu chuỗi thời gian khi đổi region, KPI hoặc periodType
  useEffect(() => {
    if (!regionCode || !requestKey) return

    let isMounted = true

    fetchRegionKpis({
      regionCode,
      kpi: selectedKpi,
      periodType,
      source: sourceCode,
    })
      .then((data) => {
        if (!isMounted) return
        setFetchResult({ key: requestKey, data, error: null })
      })
      .catch((err) => {
        if (!isMounted) return
        setFetchResult({ key: requestKey, data: null, error: err.message })
      })

    return () => {
      isMounted = false
    }
  }, [regionCode, selectedKpi, periodType, sourceCode, requestKey])

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
      // Cắt trực tiếp chuỗi ISO (YYYY-MM-DDTHH:mm...) để tránh lệch múi giờ trình duyệt
      if (periodType === 'hour' && typeof s.at === 'string' && s.at.length >= 16) {
        const day = s.at.slice(8, 10)
        const month = s.at.slice(5, 7)
        const time = s.at.slice(11, 16)
        return `${day}/${month} ${time}`
      }
      return s.at
    })

    const values = series.map((s) => (s.value !== null ? s.value : null))
    const shouldBeginAtZero =
      !isQualityKpi(currentKpiObj) || currentKpiObj?.higher_is_better === false

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
            beginAtZero: shouldBeginAtZero,
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
  }, [chartData, selectedKpi, periodType, loading, currentKpiObj])

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
            * Nguồn dữ liệu: <strong>{sourceCode}</strong> (Dữ liệu mô phỏng di động 4G)
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Đóng
          </button>
        </div>
      </div>
    </div>
  )
}
