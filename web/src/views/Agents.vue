<template>
  <div class="agents-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>智能体管理</span>
          <el-button type="primary">
            <el-icon><Plus /></el-icon>
            新建智能体
          </el-button>
        </div>
      </template>

      <el-empty description="智能体管理功能开发中..." />
    </el-card>
  </div>
</template>

<script setup>
import { Plus } from '@element-plus/icons-vue'
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
