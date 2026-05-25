<template>
  <div class="model-management">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>模型提供商</span>
              <el-button type="primary" size="small" @click="openProviderDialog()">新增提供商</el-button>
            </div>
          </template>
          <el-table :data="providers" v-loading="providerLoading" stripe highlight-current-row @current-change="handleProviderSelect">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="provider_type" label="类型" width="120" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openProviderDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteProvider(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>模型列表{{ selectedProvider ? ` - ${selectedProvider.name}` : '' }}</span>
              <el-button type="primary" size="small" :disabled="!selectedProvider" @click="openModelDialog()">新增模型</el-button>
            </div>
          </template>
          <el-table :data="models" v-loading="modelLoading" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="model_id" label="模型ID" width="180" />
            <el-table-column prop="max_tokens" label="最大Token" width="100" />
            <el-table-column prop="temperature" label="温度" width="80" />
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openModelDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="providerDialogVisible" :title="editingProviderId ? '编辑提供商' : '新增提供商'" width="500px" destroy-on-close>
      <el-form ref="providerFormRef" :model="providerForm" :rules="providerRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="providerForm.name" placeholder="请输入提供商名称" />
        </el-form-item>
        <el-form-item label="类型" prop="provider_type">
          <el-select v-model="providerForm.provider_type" placeholder="请选择类型" style="width: 100%">
            <el-option label="OpenAI" value="openai" />
            <el-option label="Azure OpenAI" value="azure_openai" />
            <el-option label="Anthropic" value="anthropic" />
            <el-option label="DashScope" value="dashscope" />
            <el-option label="ZhipuAI" value="zhipuai" />
            <el-option label="Ollama" value="ollama" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input v-model="providerForm.api_key" type="password" show-password placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="providerForm.base_url" placeholder="请输入 Base URL（可选）" />
        </el-form-item>
        <el-form-item label="租户" prop="tenant_id">
          <el-select v-model="providerForm.tenant_id" placeholder="请选择租户" style="width: 100%">
            <el-option v-for="t in tenantOptions" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleProviderSubmit">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="modelDialogVisible" :title="editingModelId ? '编辑模型' : '新增模型'" width="500px" destroy-on-close>
      <el-form ref="modelFormRef" :model="modelForm" :rules="modelRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="modelForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型ID" prop="model_id">
          <el-input v-model="modelForm.model_id" placeholder="如 gpt-4o, claude-3-5-sonnet" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider_id">
          <el-select v-model="modelForm.provider_id" placeholder="请选择提供商" style="width: 100%">
            <el-option v-for="p in providers" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大Token" prop="max_tokens">
          <el-input-number v-model="modelForm.max_tokens" :min="1" :max="128000" />
        </el-form-item>
        <el-form-item label="温度" prop="temperature">
          <el-slider v-model="modelForm.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="Top P" prop="top_p">
          <el-slider v-model="modelForm.top_p" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleModelSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  getProviders, createProvider, updateProvider, deleteProvider,
  getModels, createModel, updateModel, deleteModel,
  type ModelProvider, type ModelConfig,
} from '@/api/model'
import { getTenants, type Tenant } from '@/api/tenant'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const providerLoading = ref(false)
const modelLoading = ref(false)
const providers = ref<ModelProvider[]>([])
const models = ref<ModelConfig[]>([])
const selectedProvider = ref<ModelProvider | null>(null)
const tenantOptions = ref<Tenant[]>([])
const submitting = ref(false)

const providerDialogVisible = ref(false)
const editingProviderId = ref('')
const providerFormRef = ref<FormInstance>()
const providerForm = reactive({
  name: '',
  provider_type: '',
  api_key: '',
  base_url: '',
  tenant_id: '',
})

const providerRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
  tenant_id: [{ required: true, message: '请选择租户', trigger: 'change' }],
}

const modelDialogVisible = ref(false)
const editingModelId = ref('')
const modelFormRef = ref<FormInstance>()
const modelForm = reactive({
  name: '',
  model_id: '',
  provider_id: '',
  max_tokens: 4096,
  temperature: 0.7,
  top_p: 1.0,
})

const modelRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  provider_id: [{ required: true, message: '请选择提供商', trigger: 'change' }],
}

async function loadProviders() {
  providerLoading.value = true
  try {
    const res = await getProviders({ page: 1, page_size: 100 })
    providers.value = res.data.items
  } catch {
    ElMessage.error('加载提供商列表失败')
  } finally {
    providerLoading.value = false
  }
}

async function loadModels(providerId?: string) {
  modelLoading.value = true
  try {
    const res = await getModels({ provider_id: providerId, page: 1, page_size: 100 })
    models.value = res.data.items
  } catch {
    ElMessage.error('加载模型列表失败')
  } finally {
    modelLoading.value = false
  }
}

async function loadTenants() {
  try {
    const res = await getTenants({ page: 1, page_size: 100 })
    tenantOptions.value = res.data.items
  } catch {}
}

function handleProviderSelect(row: ModelProvider | null) {
  selectedProvider.value = row
  if (row) {
    loadModels(row.id)
  } else {
    models.value = []
  }
}

function openProviderDialog(row?: ModelProvider) {
  if (row) {
    editingProviderId.value = row.id
    providerForm.name = row.name
    providerForm.provider_type = row.provider_type
    providerForm.api_key = row.api_key
    providerForm.base_url = row.base_url
    providerForm.tenant_id = row.tenant_id
  } else {
    editingProviderId.value = ''
    providerForm.name = ''
    providerForm.provider_type = ''
    providerForm.api_key = ''
    providerForm.base_url = ''
    providerForm.tenant_id = ''
  }
  providerDialogVisible.value = true
}

async function handleProviderSubmit() {
  const valid = await providerFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingProviderId.value) {
      await updateProvider(editingProviderId.value, {
        name: providerForm.name,
        provider_type: providerForm.provider_type,
        api_key: providerForm.api_key,
        base_url: providerForm.base_url,
      })
      ElMessage.success('更新成功')
    } else {
      await createProvider(providerForm)
      ElMessage.success('创建成功')
    }
    providerDialogVisible.value = false
    loadProviders()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeleteProvider(row: ModelProvider) {
  await ElMessageBox.confirm(`确定删除提供商「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteProvider(row.id)
    ElMessage.success('删除成功')
    if (selectedProvider.value?.id === row.id) {
      selectedProvider.value = null
      models.value = []
    }
    loadProviders()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

function openModelDialog(row?: ModelConfig) {
  if (row) {
    editingModelId.value = row.id
    modelForm.name = row.name
    modelForm.model_id = row.model_id
    modelForm.provider_id = row.provider_id
    modelForm.max_tokens = row.max_tokens
    modelForm.temperature = row.temperature
    modelForm.top_p = row.top_p
  } else {
    editingModelId.value = ''
    modelForm.name = ''
    modelForm.model_id = ''
    modelForm.provider_id = selectedProvider.value?.id || ''
    modelForm.max_tokens = 4096
    modelForm.temperature = 0.7
    modelForm.top_p = 1.0
  }
  modelDialogVisible.value = true
}

async function handleModelSubmit() {
  const valid = await modelFormRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (editingModelId.value) {
      await updateModel(editingModelId.value, {
        name: modelForm.name,
        model_id: modelForm.model_id,
        max_tokens: modelForm.max_tokens,
        temperature: modelForm.temperature,
        top_p: modelForm.top_p,
      })
      ElMessage.success('更新成功')
    } else {
      await createModel(modelForm)
      ElMessage.success('创建成功')
    }
    modelDialogVisible.value = false
    if (selectedProvider.value) loadModels(selectedProvider.value.id)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeleteModel(row: ModelConfig) {
  await ElMessageBox.confirm(`确定删除模型「${row.name}」？`, '确认删除', { type: 'warning' })
  try {
    await deleteModel(row.id)
    ElMessage.success('删除成功')
    if (selectedProvider.value) loadModels(selectedProvider.value.id)
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  loadProviders()
  loadTenants()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
