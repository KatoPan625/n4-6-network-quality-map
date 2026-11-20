import React from 'react'
import { COLORS } from '../utils/colorScale'

/**
 * Component Chú giải (Legend) đáp ứng các tiêu chí nghiệm thu của Issue #5:
 * 1. Đơn vị đo KPI
 * 2. Thời gian cập nhật dữ liệu
 * 3. Nhãn "Dữ liệu mô phỏng"
 */
export default function Legend({ kpiMeta, periodAt, updatedAt, sourceMeta }) {
  const isTraffic = kpiMeta?.kpi_code === 'traffic'

  // Format thời gian cập nhật
  const formattedUpdate = updatedAt
    ? new Date(updatedAt).toLocaleString('vi-VN', {
        timeZone: 'Asia/Ho_Chi_Minh',
        dateStyle: 'medium',
        timeStyle: 'medium',
      })
    : 'Chưa có mốc cập nhật'

  const formattedPeriod = periodAt
    ? periodAt.replace('T', ' ')
    : 'N/A'

  return (
    <div className="map-legend-card">
      <div className="legend-header">
        <h4 className="legend-title">{kpiMeta?.kpi_name || 'Chỉ số KPI'}</h4>
        <div className="legend-meta">
          <span className="meta-item">
            <strong>Đơn vị:</strong>{' '}
            <span className="badge badge-unit">{kpiMeta?.unit || 'N/A'}</span>
          </span>
          <span className="meta-item">
            <strong>Thời điểm (at):</strong> {formattedPeriod}
          </span>
          <span className="meta-item">
            <strong>Cập nhật:</strong> {formattedUpdate}
          </span>
        </div>
      </div>

      {/* Nhãn Dữ liệu mô phỏng bắt buộc */}
      <div className="simulated-badge-box">
        <span className="simulated-indicator">⚠️</span>
        <div>
          <strong className="simulated-text">Dữ liệu mô phỏng</strong>
          <div className="simulated-subtext">
            Nguồn: {sourceMeta?.source_code || 'BE-SAMPLE'} ({sourceMeta?.data_nature || 'simulated'})
          </div>
        </div>
      </div>

      {/* Thang màu chất lượng */}
      <div className="legend-items">
        <div className="legend-subtitle">Quy ước mức chất lượng:</div>
        {!isTraffic ? (
          <>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: COLORS.good }}></span>
              <span>Tốt {kpiMeta?.kpi_code === 'cssr' ? '(≥ 98%)' : kpiMeta?.kpi_code === 'service_drop_all' ? '(≤ 2%)' : kpiMeta?.kpi_code === 'user_throughput' ? '(≥ 16 Mbps)' : ''}</span>
            </div>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: COLORS.medium }}></span>
              <span>Trung bình {kpiMeta?.kpi_code === 'cssr' ? '(95% - 98%)' : kpiMeta?.kpi_code === 'service_drop_all' ? '(2% - 5%)' : kpiMeta?.kpi_code === 'user_throughput' ? '(5 - 16 Mbps)' : ''}</span>
            </div>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: COLORS.poor }}></span>
              <span>Kém {kpiMeta?.kpi_code === 'cssr' ? '(< 95%)' : kpiMeta?.kpi_code === 'service_drop_all' ? '(> 5%)' : kpiMeta?.kpi_code === 'user_throughput' ? '(< 5 Mbps)' : ''}</span>
            </div>
          </>
        ) : (
          <>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: '#1d4ed8' }}></span>
              <span>Lưu lượng cao</span>
            </div>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: '#60a5fa' }}></span>
              <span>Lưu lượng trung bình</span>
            </div>
            <div className="legend-row">
              <span className="color-box" style={{ backgroundColor: '#93c5fd' }}></span>
              <span>Lưu lượng thấp</span>
            </div>
          </>
        )}

        {/* Trạng thái dữ liệu */}
        <div className="legend-divider"></div>
        <div className="legend-row">
          <span className="color-box dashed-border" style={{ backgroundColor: '#fed7aa', borderColor: COLORS.partialBorder }}></span>
          <span>Dữ liệu một phần (thiếu cell)</span>
        </div>
        <div className="legend-row">
          <span className="color-box" style={{ backgroundColor: COLORS.noTraffic }}></span>
          <span>Không có lưu lượng (traffic = 0)</span>
        </div>
        <div className="legend-row">
          <span className="color-box" style={{ backgroundColor: COLORS.missing }}></span>
          <span>Không có dữ liệu (missing)</span>
        </div>
      </div>
    </div>
  )
}
