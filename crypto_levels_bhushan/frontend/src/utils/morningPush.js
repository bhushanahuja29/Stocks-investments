/**
 * @deprecated Import from pushNotifications.js — kept for backward compatibility.
 */
export {
  isPushSupported,
  registerServiceWorker,
  requestNotificationPermission,
  sendLocalTestNotification,
  fetchVapidPublicKey,
  subscribeToPush,
  unsubscribeFromPush,
  sendServerTestPush,
  isPushSubscribed,
  ensurePushSubscription,
  getPushSubscriptionState,
  fetchPushStatus,
} from './pushNotifications';
