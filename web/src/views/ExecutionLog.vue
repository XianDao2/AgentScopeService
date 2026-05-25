<template>
  <div class="execution-log">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>执行日志</span>
          <div class="filter-bar">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable size="small" style="width: 120px; margin-right: 8px">
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
            <el-date-picker
              v-model="filterDate"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              value-format="YYYY-MM-DD"
              style="width: 260px; margin-right: 8px"
            />
            <el-button type="primary" size="small" @click="loadData">查询</el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="16" style="margin-bottom: 16px" v-if="stats">
        <el-col :span="6">
          <el-statistic title="总调用次数" :value="stats.total_calls" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="输入 Token" :value="stats.total_input_tokens" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="输出 Token" :value="stats.total_output_tokens" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功率" :value="stats.success_rate * 100" suffix="%" :precision="1" />
        </el-col>
      </el-row>

      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="agent_name" label="Agent" width="150" />
        <el-table-column prop="event_type" label="事件类型" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="input_tokens" label="输入Token" width="120" />
        <el-table-column prop="output_tokens" label="输出Token" width="120" />
        <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getExecutionLogs, getExecutionStats, type ExecutionLog } from '@/api/executionLog'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const logs = ref<ExecutionLog[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStatus = ref('')
const filterDate = ref<[string, string] | null>(null)
const stats = ref<{
  total_calls: number
  total_input_tokens: number
  total_output_tokens: number
  avg_duration_ms: number
  success_rate: number
} | null>(null)

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterDate.value) {
      params.start_date = filterDate.value[0]
      params.end_date = filterDate.value[1]
    }
    const res = await getExecutionLogs(params)
    logs.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载执行日志失败')
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const params: any = {}
    if (filterDate.value) {
      params.start_date = filterDate.value[0]
      params.end_date = filterDate.value[1]
    }
    const res = await getExecutionStats(params)
    stats.value = res.data
  } catch {}
}

onMounted(() => {
  loadData()
  loadStats()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-bar {
  display: flex;
  align-items: center;
}
.error-text {
  color: #f56c6c;
  font-size: 12px;
}
.text-muted {
  color: #c0c4cc;
}
</style>
