<template>
  <div class="knowledge-base">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-button type="primary" @click="openDialog()">新增知识库</el-button>
        </div>
      </template>
      <el-table :data="knowledgeBases" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="embedding_model_name" label="嵌入模型" width="150" />
        <el-table-column label="统计" width="200">
          <template #default="{ row }">
            <KnowledgeStats
              :document-count="row.document_count"
              :chunk-count="row.chunk_count"
              :status="row.status"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="goDocuments(row)">文档管理</el-button>
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑知识库' : '新增知识库'" width="500px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="嵌入模型" prop="embedding_model_id">
          <el-select v-model="form.embedding_model_id" placeholder="请选择嵌入模型" style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分块大小" prop="chunk_size">
          <el-input-number v-model="form.chunk_size" :min="128" :max="8192" :step="128" />
        </el-form-item>
        <el-form-item label="分块重叠" prop="chunk_overlap">
          <el-input-number v-model="form.chunk_overlap" :min="0" :max="1024" :step="32" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  getKnowledgeBases, createKnowledgeBase, updateKnowledgeBase, deleteKnowledgeBase,
  type KnowledgeBase,
} from '@/api/knowledge'
import { getModels, type ModelConfig } from '@/api/model'
import KnowledgeStats from '@/components/KnowledgeStats.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const knowledgeBases = ref<KnowledgeBase[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const modelOptions = ref<ModelConfig[]>([])

const dialogVisible = ref(false)
const editingId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  embedding_model_id: '',
  chunk_size: 512,
  chunk_overlap: 64,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  embedding_model_id: [{ required: true, message: '请选择嵌入模型', trigger: 'change' }],
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getKnowledgeBases({ page: page.value, page_size: pageSize.value })
    knowledgeBases.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

async function loadModels() {
  try {
    const res = await getModels({ page: 1, page_size: 100 })
    modelOptions.value = res.data.items
  } catch {}
}

function openDialog(row?: KnowledgeBase) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.description = row.description
    form.embedding_model_id = row.embedding_model_id
    form.chunk_size = row.chunk_size
    form.chunk_overlap = row.chunk_overlap
  } else {
    editingId.value = ''
    form.name = ''
    form.description = ''
    form.embedding_model_id = ''
    form.chunk_size = 512
    form.chunk_overlap = 64
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateKnowledgeBase(editingId.value, {
        name: form.name,
        description: form.description,
        chunk_size: form.chunk_size,
        chunk_overlap: form.chunk_overlap,
      })
      ElMessage.success('更新成功')
    } else {
      await createKnowledgeBase(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: KnowledgeBase) {
  await ElMessageBox.confirm(`确定删除知识库「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteKnowledgeBase(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function goDocuments(row: KnowledgeBase) {
  router.push({ name: 'KnowledgeDocument', params: { id: row.id } })
}

onMounted(() => {
  loadData()
  loadModels()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
