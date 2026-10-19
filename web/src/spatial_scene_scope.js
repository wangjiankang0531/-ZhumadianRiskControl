// Display scope only: registration, business classification and authorization stay unchanged.
import {inTopic,spatialObject,topics} from './spatial_catalog.js';
export function inSceneTopic(feature,topic,catalog=null) {
 const category=spatialObject(feature,catalog).category;
 return inTopic(feature,topic,catalog)||(topic==='emergency'&&['enterprise','enterprise-boundary'].includes(category));
}
export function scopedSceneObjects(layers,topic='all',category='all',catalog=null) {
 return (layers??[]).flatMap(layer=>layer.features.filter(feature=>inSceneTopic(feature,topic,catalog)&&(category==='all'||spatialObject(feature,catalog).category===category)).map(feature=>({feature,layer})));
}
export function sceneTopicCounts(layers,catalog=null) {
 return Object.fromEntries(['all',...Object.keys(topics)].map(topic=>[topic,scopedSceneObjects(layers,topic,'all',catalog).length]));
}
