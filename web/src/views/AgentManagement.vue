<template>
  <div class="agent-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Agent 管理</span>
          <el-button type="primary" @click="openDialog()">新增 Agent</el-button>
        </div>
      </template>
      <el-table :data="agents" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="agent_type" label="类型" width="120" />
        <el-table-column prop="model_name" label="模型" width="150" />
        <el-table-column prop="tool_group_names" label="工具组" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="name in row.tool_group_names" :key="name" size="small" style="margin-right: 4px">{{ name }}</el-tag>
            <span v-if="!row.tool_group_names?.length" class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="goChat(row)">对话</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑 Agent' : '新增 Agent'" width="600px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="类型" prop="agent_type">
          <el-select v-model="form.agent_type" placeholder="请选择类型" style="width: 100%">
            <el-option label="Assistant" value="assistant" />
            <el-option label="ReAct Agent" value="react" />
            <el-option label="RAG Agent" value="rag" />
            <el-option label="Workflow" value="workflow" />
          </el-select>
        </el-form-item>
        <el-form-item label="系统提示词" prop="sys_prompt">
          <el-input v-model="form.sys_prompt" type="textarea" :rows="4" placeholder="请输入系统提示词" />
        </el-form-item>
        <el-form-item label="模型" prop="model_id">
          <el-select v-model="form.model_id" placeholder="请选择模型" style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工具组" prop="tool_group_ids">
          <el-select v-model="form.tool_group_ids" multiple placeholder="请选择工具组" style="width: 100%">
            <el-option v-for="tg in toolGroupOptions" :key="tg.id" :label="tg.name" :value="tg.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="知识库" prop="knowledge_base_ids">
          <el-select v-model="form.knowledge_base_ids" multiple placeholder="请选择知识库" style="width: 100%">
            <el-option v-for="kb in knowledgeOptions" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大重试" prop="max_retries">
          <el-input-number v-model="form.max_retries" :min="0" :max="10" />
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
import { getAgents, createAgent, updateAgent, deleteAgent, type AgentDefinition } from '@/api/agent'
import { getModels, type ModelConfig } from '@/api/model'
import { getToolGroups, type ToolGroup } from '@/api/toolGroup'
import { getKnowledgeBases, type KnowledgeBase } from '@/api/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const agents = ref<AgentDefinition[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const modelOptions = ref<ModelConfig[]>([])
const toolGroupOptions = ref<ToolGroup[]>([])
const knowledgeOptions = ref<KnowledgeBase[]>([])

const dialogVisible = ref(false)
const editingId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  agent_type: '',
  sys_prompt: '',
  model_id: '',
  tool_group_ids: [] as string[],
  knowledge_base_ids: [] as string[],
  max_retries: 3,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  agent_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  model_id: [{ required: true, message: '请选择模型', trigger: 'change' }],
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const res = await getAgents({ page: page.value, page_size: pageSize.value })
    agents.value = res.data.items
    total.value = res.data.total
  } catch {
    ElMessage.error('加载 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

async function loadOptions() {
  try {
    const [modelsRes, tgRes, kbRes] = await Promise.allSettled([
      getModels({ page: 1, page_size: 100 }),
      getToolGroups({ page: 1, page_size: 100 }),
      getKnowledgeBases({ page: 1, page_size: 100 }),
    ])
    if (modelsRes.status === 'fulfilled') modelOptions.value = modelsRes.value.data.items
    if (tgRes.status === 'fulfilled') toolGroupOptions.value = tgRes.value.data.items
    if (kbRes.status === 'fulfilled') knowledgeOptions.value = kbRes.value.data.items
  } catch {}
}

function openDialog(row?: AgentDefinition) {
  if (row) {
    editingId.value = row.id
    form.name = row.name
    form.agent_type = row.agent_type
    form.sys_prompt = row.sys_prompt
    form.model_id = row.model_id
    form.tool_group_ids = [...(row.tool_group_ids || [])]
    form.knowledge_base_ids = [...(row.knowledge_base_ids || [])]
    form.max_retries = row.max_retries
  } else {
    editingId.value = ''
    form.name = ''
    form.agent_type = ''
    form.sys_prompt = ''
    form.model_id = ''
    form.tool_group_ids = []
    form.knowledge_base_ids = []
    form.max_retries = 3
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingId.value) {
      await updateAgent(editingId.value, {
        name: form.name,
        agent_type: form.agent_type,
        sys_prompt: form.sys_prompt,
        model_id: form.model_id,
        tool_group_ids: form.tool_group_ids,
        knowledge_base_ids: form.knowledge_base_ids,
        max_retries: form.max_retries,
      })
      ElMessage.success('更新成功')
    } else {
      await createAgent(form)
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

async function handleDelete(row: AgentDefinition) {
  await ElMessageBox.confirm(`确定删除 Agent「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteAgent(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function goChat(row: AgentDefinition) {
  router.push({ name: 'AgentChat', params: { id: row.id } })
}

onMounted(() => {
  loadData()
  loadOptions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.text-muted {
  color: #c0c4cc;
}
</style>
