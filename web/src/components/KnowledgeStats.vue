<template>
  <div class="knowledge-stats">
    <el-row :gutter="16">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ documentCount }}</div>
          <div class="stat-label">文档数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ chunkCount }}</div>
          <div class="stat-label">分块数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">
            <el-tag :type="statusType" size="small">{{ statusLabel }}</el-tag>
          </div>
          <div class="stat-label">状态</div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  documentCount: number
  chunkCount: number
  status: string
}>()

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    ready: '就绪',
    indexing: '索引中',
    error: '错误',
    empty: '空',
  }
  return map[props.status] || props.status
})

const statusType = computed(() => {
  const map: Record<string, string> = {
    ready: 'success',
    indexing: 'warning',
    error: 'danger',
    empty: 'info',
  }
  return map[props.status] || 'info'
})
</script>

<style scoped>
.knowledge-stats {
  margin: 8px 0;
}
.stat-card {
  text-align: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 6px;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 12px;
  color: #909399;
}
</style>
