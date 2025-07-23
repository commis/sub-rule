<template>
  <div class="channels-view">
    <div class="toolbar">
      <button @click="logout">退出登录</button>
      <button @click="saveChannels">保存频道列表</button>
    </div>
    <div class="main-content">
      <ChannelList 
        :channels="channels" 
        :selectedChannelIndex="selectedChannelIndex"
        @select="onChannelSelect"
        @add="onAddChannel"
      />
      <Player :selectedChannel="selectedChannel" />
      <ChannelEdit 
        v-if="isEditing"
        :channel="editingChannel"
        :isEditMode="isEditMode"
        @save="onSaveChannel"
        @cancel="onCancelEdit"
        @delete="onDeleteChannel"
      />
    </div>
  </div>
</template>

<script>
import ChannelList from '@/components/ChannelList.vue'
import Player from '@/components/Player.vue'
import ChannelEdit from '@/components/ChannelEdit.vue'

export default {
  components: {
    ChannelList,
    Player,
    ChannelEdit
  },
  data() {
    return {
      channels: [
        { name: '央视综合', url: 'https://example.com/cctv1.m3u8', category: '新闻' },
        { name: '央视财经', url: 'https://example.com/cctv2.m3u8', category: '财经' },
        { name: '卫视娱乐', url: 'https://example.com/entertainment.m3u8', category: '娱乐' }
      ],
      selectedChannelIndex: -1,
      isEditing: false,
      editingChannel: { name: '', url: '', category: '' },
      isEditMode: false
    }
  },
  computed: {
    selectedChannel() {
      return this.channels[this.selectedChannelIndex] || null
    }
  },
  mounted() {
    // 从本地存储加载频道列表
    const savedChannels = localStorage.getItem('iptvChannels')
    if (savedChannels) {
      this.channels = JSON.parse(savedChannels)
    }
  },
  methods: {
    onChannelSelect(index) {
      this.selectedChannelIndex = index
      this.isEditing = false
    },
    onAddChannel() {
      this.editingChannel = { name: '', url: '', category: '' }
      this.isEditMode = false
      this.isEditing = true
    },
    onSaveChannel(channel) {
      if (this.isEditMode) {
        // 更新现有频道
        this.channels[this.selectedChannelIndex] = channel
      } else {
        // 添加新频道
        this.channels.push(channel)
        this.selectedChannelIndex = this.channels.length - 1
      }
      this.isEditing = false
      this.saveChannels()
    },
    onCancelEdit() {
      this.isEditing = false
    },
    onDeleteChannel() {
      this.channels.splice(this.selectedChannelIndex, 1)
      this.selectedChannelIndex = -1
      this.isEditing = false
      this.saveChannels()
    },
    saveChannels() {
      localStorage.setItem('iptvChannels', JSON.stringify(this.channels))
      alert('频道列表已保存')
    },
    logout() {
      localStorage.removeItem('isLoggedIn')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.channels-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.toolbar {
  padding: 10px;
  background-color: #f5f5f5;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.toolbar button {
  padding: 8px 15px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.main-content {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}
</style>  