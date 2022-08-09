import Vue from 'vue';
import { ContentNode, Channel } from '../../../shared/data/resources';
import client from 'shared/client';

export function loadChannel(context, { staging = false } = {}) {
  return context
    .dispatch('channel/loadChannel', context.state.currentChannelId, { root: true })
    .then(channel => {
      if (channel) {
        Vue.$analytics.trackCurrentChannel(channel, staging);
      }
      return channel;
    });
}

export function loadChannelSize(context, rootId) {
  return ContentNode.getResourceSize(rootId);
}

export function loadCurrentChannelStagingDiff(context) {
  return client
    .get(window.Urls.getNodeDiff(context.getters.stagingId, context.getters.rootId))
    .then(response => {
      context.commit('SAVE_CURRENT_CHANNEL_STAGING_DIFF', response.data.stats);
    })
    .catch(error => {
      // Diff is being generated, so try again in 5 seconds
      if (error.response && error.response.status === 302) {
        context.commit('SAVE_CURRENT_CHANNEL_STAGING_DIFF', { _status: 'loading' });
        setTimeout(() => {
          loadCurrentChannelStagingDiff(context);
        }, 5000);
      } else {
        context.commit('SAVE_CURRENT_CHANNEL_STAGING_DIFF', { _status: 'error' });
      }
    });
}

export function reloadCurrentChannelStagingDiff(context) {
  return client
    .post(window.Urls.generate_node_diff(context.getters.stagingId, context.getters.rootId))
    .then(() => {
      context.commit('SAVE_CURRENT_CHANNEL_STAGING_DIFF', { _status: 'loading' });
      setTimeout(() => {
        loadCurrentChannelStagingDiff(context);
      }, 5000);
    });
}

export function deployCurrentChannel(context) {
  let payload = {
    channel_id: context.state.currentChannelId,
  };
  return client.post(window.Urls.activate_channel(), payload);
}

export function publishChannel(context, version_notes) {
  return Channel.publish(context.state.currentChannelId, version_notes);
}

export function stopTask(context, task) {
  if (task && task.task_name === 'export-channel') {
    return Channel.clearPublish(context.state.currentChannelId).then(() => {
      return context.dispatch('task/deleteTask', task, { root: true });
    });
  } else if (task) {
    return context.dispatch('task/deleteTask', task, { root: true });
  } else {
    Promise.resolve();
  }
}
