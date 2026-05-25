<template>
  <div class="knowledge-document">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-button link @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回知识库
            </el-button>
            <span style="margin-left: 12px">文档管理 - {{ kbName }}</span>
          </div>
          <el-upload
            :show-file-list="false"
            :before-upload="handleUpload"
            :action="''"
            :auto-upload="false"
          >
            <el-button type="primary">上传文档</el-button>
          </el-upload>
        </div>
      </template>
      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="file_size" label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="分块数" width="100" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
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
import { useRoute, useRouter } from 'vue-router'
import {
  getKnowledgeBase, getDocuments, uploadDocument, deleteDocument,
  type KnowledgeDocument,
} from '@/api/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const kbId = route.params.id as string
const kbName = ref('')

const loading = ref(false)
const documents = ref<KnowledgeDocument[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

function formatSize(bytes: number) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function statusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getDocuments(kbId, { page: page.value, page_size: pageSize.value })
    documents.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload(file: File) {
  try {
    await uploadDocument(kbId, file)
    ElMessage.success('上传成功，文档正在处理中')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  }
  return false
}

async function handleDelete(row: KnowledgeDocument) {
  await ElMessageBox.confirm(`确定删除文档「${row.filename}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteDocument(kbId, row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function goBack() {
  router.push({ name: 'KnowledgeBase' })
}

onMounted(async () => {
  try {
    const res = await getKnowledgeBase(kbId)
    kbName.value = res.data.name
  } catch {}
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left {
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
