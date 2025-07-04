import { useState } from 'react'
import { useSelector } from 'react-redux'
import DatePicker from 'react-datepicker'
import "react-datepicker/dist/react-datepicker.css"
import type { RootState } from '../../store'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import jsPDF from 'jspdf'
import 'jspdf-autotable'

type ReportType = 'sales' | 'inventory' | 'users'
type ExportFormat = 'csv' | 'xlsx' | 'pdf'

export default function ReportsPage() {
  const { filters } = useSelector((state: RootState) => state.admin)
  const [reportType, setReportType] = useState<ReportType>('sales')
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv')
  const [startDate, setStartDate] = useState<Date>(new Date(filters.start_date))
  const [endDate, setEndDate] = useState<Date>(new Date(filters.end_date))

  // Commented out for now since we're using generateLocalReport
  // const handleGenerateReport = async () => {
  //   const reportFilters = {
  //     ...filters,
  //     start_date: startDate.toISOString().split('T')[0],
  //     end_date: endDate.toISOString().split('T')[0],
  //   }

  //   dispatch(setFilters(reportFilters))
    
  //   // For backend integration
  //   await dispatch(generateReport({
  //     type: reportType,
  //     filters: reportFilters,
  //     format: exportFormat,
  //   }))
  // }

  const generateLocalReport = () => {
    // This is a placeholder for local report generation
    // In a real app, this would use actual data from the API
    const sampleData = {
      sales: [
        { date: '2024-01-01', orders: 15, revenue: 1250.00, tax: 125.00, shipping: 50.00 },
        { date: '2024-01-02', orders: 22, revenue: 1890.00, tax: 189.00, shipping: 80.00 },
        { date: '2024-01-03', orders: 18, revenue: 1560.00, tax: 156.00, shipping: 65.00 },
      ],
      inventory: [
        { product: 'Custom T-Shirt', sku: 'TS001', stock: 45, sold: 155, revenue: 3875.00 },
        { product: 'Photo Mug', sku: 'MG001', stock: 23, sold: 87, revenue: 1305.00 },
        { product: 'Canvas Print', sku: 'CP001', stock: 12, sold: 43, revenue: 2150.00 },
      ],
      users: [
        { name: 'John Doe', email: 'john@example.com', joined: '2024-01-15', orders: 5, spent: 450.00 },
        { name: 'Jane Smith', email: 'jane@example.com', joined: '2024-01-20', orders: 3, spent: 280.00 },
        { name: 'Bob Johnson', email: 'bob@example.com', joined: '2024-01-25', orders: 7, spent: 625.00 },
      ],
    }

    const data = sampleData[reportType]
    const filename = `${reportType}-report-${new Date().toISOString().split('T')[0]}`

    switch (exportFormat) {
      case 'csv':
        exportToCSV(data, filename)
        break
      case 'xlsx':
        exportToXLSX(data, filename)
        break
      case 'pdf':
        exportToPDF(data, filename, reportType)
        break
    }
  }

  const exportToCSV = (data: any[], filename: string) => {
    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => row[header]).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    saveAs(blob, `${filename}.csv`)
  }

  const exportToXLSX = (data: any[], filename: string) => {
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Report')
    XLSX.writeFile(wb, `${filename}.xlsx`)
  }

  const exportToPDF = (data: any[], filename: string, type: ReportType) => {
    const doc = new jsPDF()
    
    // Add title
    doc.setFontSize(20)
    doc.text(`${type.charAt(0).toUpperCase() + type.slice(1)} Report`, 14, 22)
    
    // Add date range
    doc.setFontSize(12)
    doc.text(`Period: ${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`, 14, 32)
    
    // Add table
    const headers = Object.keys(data[0])
    const rows = data.map(item => headers.map(header => item[header]))
    
    ;(doc as any).autoTable({
      head: [headers],
      body: rows,
      startY: 40,
    })
    
    doc.save(`${filename}.pdf`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Reports & Analytics</h1>
        <p className="text-gray-600">Generate and export detailed business reports</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-6">Generate Report</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value as ReportType)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="sales">Sales Report</option>
              <option value="inventory">Inventory Report</option>
              <option value="users">Users Report</option>
            </select>
          </div>

          {/* Export Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Export Format
            </label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="csv">CSV</option>
              <option value="xlsx">Excel (XLSX)</option>
              <option value="pdf">PDF</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <DatePicker
              selected={startDate}
              onChange={(date: Date | null) => date && setStartDate(date)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              dateFormat="yyyy-MM-dd"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <DatePicker
              selected={endDate}
              onChange={(date: Date | null) => date && setEndDate(date)}
              className="w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              dateFormat="yyyy-MM-dd"
            />
          </div>
        </div>

        {/* Additional Filters based on Report Type */}
        {reportType === 'sales' && (
          <div className="mt-6 p-4 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-800">
              Sales report includes: Order details, revenue, tax, shipping costs, and payment methods
            </p>
          </div>
        )}

        {reportType === 'inventory' && (
          <div className="mt-6 p-4 bg-green-50 rounded-md">
            <p className="text-sm text-green-800">
              Inventory report includes: Product stock levels, sales volume, and revenue per product
            </p>
          </div>
        )}

        {reportType === 'users' && (
          <div className="mt-6 p-4 bg-purple-50 rounded-md">
            <p className="text-sm text-purple-800">
              Users report includes: Customer details, registration dates, order history, and total spending
            </p>
          </div>
        )}

        <div className="mt-6 flex gap-4">
          <button
            onClick={generateLocalReport}
            className="px-6 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Generate Report
          </button>
        </div>
      </div>

      {/* Quick Reports */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Monthly Sales Summary</h3>
          <p className="text-gray-600 mb-4">Quick overview of this month's sales performance</p>
          <button
            onClick={() => {
              setReportType('sales')
              setStartDate(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
              setEndDate(new Date())
              generateLocalReport()
            }}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Generate Monthly Report
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Low Stock Alert</h3>
          <p className="text-gray-600 mb-4">Products with stock levels below threshold</p>
          <button
            onClick={() => {
              setReportType('inventory')
              generateLocalReport()
            }}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            View Low Stock Items
          </button>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">New Users Report</h3>
          <p className="text-gray-600 mb-4">Users who joined in the last 30 days</p>
          <button
            onClick={() => {
              setReportType('users')
              setStartDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
              setEndDate(new Date())
              generateLocalReport()
            }}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Generate User Report
          </button>
        </div>
      </div>

      {/* Report Templates */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Report Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">End of Year Report</h4>
            <p className="text-sm text-gray-600 mb-3">Comprehensive yearly business analysis</p>
            <button className="text-sm text-blue-600 hover:text-blue-800">Configure Template</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">Tax Report</h4>
            <p className="text-sm text-gray-600 mb-3">Sales tax and revenue breakdown</p>
            <button className="text-sm text-blue-600 hover:text-blue-800">Configure Template</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">Customer Insights</h4>
            <p className="text-sm text-gray-600 mb-3">Customer behavior and purchase patterns</p>
            <button className="text-sm text-blue-600 hover:text-blue-800">Configure Template</button>
          </div>
          <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">Product Performance</h4>
            <p className="text-sm text-gray-600 mb-3">Best and worst performing products</p>
            <button className="text-sm text-blue-600 hover:text-blue-800">Configure Template</button>
          </div>
        </div>
      </div>
    </div>
  )
}