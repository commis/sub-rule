<template>
  <div class="channel-list">
    <h3>频道列表</h3>
    <div class="search-bar">
      <input v-model="searchQuery" placeholder="搜索频道...">
      <button @click="addChannel">添加频道</button>
    </div>
    <ul>
      <li v-for="(channel, index) in filteredChannels" :key="index"
          :class="{ active: selectedChannelIndex === index }"
          @click="selectChannel(index)">
        {{ channel.name }}
      </li>
    </ul>
  </div>
</template>

<script>
export default {
  props: {
    channels: {
      type: Array,
      default: () => []
    },
    selectedChannelIndex: {
      type: Number,
      default: -1
    }
  },
  data() {
    return {
      searchQuery: ''
    }
  },
  computed: {
    filteredChannels() {
      return this.channels.filter(channel => 
        channel.name.toLowerCase().includes(this.searchQuery.toLowerCase())
      )
    }
  },
  methods: {
    selectChannel(index) {
      this.$emit('select', index)
    },
    addChannel() {
      this.$emit('add')
    }
  }
}
</script>

<style scoped>
.channel-list {
  padding: 10px;
  border-right: 1px solid #eee;
  min-width: 200px;
  max-height: 500px;
  overflow-y: auto;
}

.search-bar {
  margin-bottom: 10px;
  display: flex;
  gap: 5px;
}

.search-bar input {
  flex-grow: 1;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 3px;
}

.search-bar button {
  padding: 5px 10px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

li {
  padding: 8px;
  margin-bottom: 5px;
  cursor: pointer;
  border-radius: 3px;
}

li:hover {
  background-color: #f0f0f0;
}

li.active {
  background-color: #42b983;
  color: white;
}
</style>  