import {checkedProjectFileName,checkedProjectFileList,checkedProjectFile,checkedProjectFileReceipt,sameProjectDocument} from './project_file_contract.js';
import {checkedSceneProject,sceneProjectName} from './scene_project.js';
export function checkedSceneFileName(name){checkedProjectFileName(name);return sceneProjectName(name);}
export function checkedSceneFileList(value){const result=checkedProjectFileList(value);for(const row of result.files)checkedSceneFileName(row.name);return result;}
export function checkedSceneFile(value,name){checkedSceneFileName(name);checkedProjectFile({...value,document:value?.document?.landscape},name);return {...structuredClone(value),document:checkedSceneProject(value.document)};}
export function checkedSceneFileReceipt(value,name){checkedSceneFileName(name);return checkedProjectFileReceipt(value,name);}
export const sameSceneDocument=sameProjectDocument;
