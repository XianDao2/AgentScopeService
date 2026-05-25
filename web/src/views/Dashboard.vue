<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #ecf5ff; color: #409eff">
            <el-icon :size="28"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f0f9eb; color: #67c23a">
            <el-icon :size="28"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.agentCount }}</div>
            <div class="stat-label">Agent 数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c">
            <el-icon :size="28"><Cpu /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.modelCount }}</div>
            <div class="stat-label">模型数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #fef0f0; color: #f56c6c">
            <el-icon :size="28"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.executionCount }}</div>
            <div class="stat-label">执行次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>最近执行日志</span>
          </template>
          <el-table :data="recentLogs" stripe size="small">
            <el-table-column prop="agent_name" label="Agent" />
            <el-table-column prop="event_type" label="类型" width="100" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration_ms" label="耗时(ms)" width="100" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="平台版本">v2.0.0</el-descriptions-item>
            <el-descriptions-item label="当前租户">{{ authStore.currentTenantName }}</el-descriptions-item>
            <el-descriptions-item label="当前用户">{{ authStore.user?.username }}</el-descriptions-item>
            <el-descriptions-item label="用户角色">
              <el-tag v-for="role in authStore.user?.roles" :key="role" size="small" style="margin-right: 4px">
                {{ role }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getAgents } from '@/api/agent'
import { getUsers } from '@/api/user'
import { getModels } from '@/api/model'
import { getExecutionLogs } from '@/api/executionLog'
import { User, ChatDotRound, Cpu, Document } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const stats = reactive({
  userCount: 0,
  agentCount: 0,
  modelCount: 0,
  executionCount: 0,
})

const recentLogs = ref<any[]>([])

import { ref } from 'vue'

onMounted(async () => {
  try {
    const [usersRes, agentsRes, modelsRes, logsRes] = await Promise.allSettled([
      getUsers({ page: 1, page_size: 1 }),
      getAgents({ page: 1, page_size: 1 }),
      getModels({ page: 1, page_size: 1 }),
      getExecutionLogs({ page: 1, page_size: 5 }),
    ])
    if (usersRes.status === 'fulfilled') stats.userCount = usersRes.value.data.total
    if (agentsRes.status === 'fulfilled') stats.agentCount = agentsRes.value.data.total
    if (modelsRes.status === 'fulfilled') stats.modelCount = modelsRes.value.data.total
    if (logsRes.status === 'fulfilled') {
      stats.executionCount = logsRes.value.data.total
      recentLogs.value = logsRes.value.data.items
    }
  } catch {}
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}
.stat-card {
  display: flex;
  align-items: center;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}
.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-info {
  flex: 1;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
</style>
