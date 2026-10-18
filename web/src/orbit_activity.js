// Stop advancing OrbitControls after it reports a settled frame. Actual input,
// programmatic control changes and auto-rotation still wake it normally.
export class OrbitActivity{
 constructor(controls){this.controls=controls;this.active=true;this.disposed=false;this.wake=()=>{this.active=true;};controls.addEventListener('start',this.wake);controls.addEventListener('change',this.wake);}
 update(deltaTime){if(this.disposed||!this.active&&!this.controls.autoRotate)return false;this.active=false;const changed=this.controls.update(deltaTime);if(changed||this.controls.autoRotate)this.active=true;return changed;}
 dispose(){this.controls.removeEventListener('start',this.wake);this.controls.removeEventListener('change',this.wake);this.disposed=true;this.active=false;}
}
