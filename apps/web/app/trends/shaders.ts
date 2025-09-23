export const streamlineVertex = /* glsl */`
  precision highp float;
  attribute float aHue;
  attribute float aRadius;
  attribute float aAngle;
  attribute float aSpeed;
  attribute float aThick;
  varying float vHue;
  varying vec2 vUvV;
  uniform float u_time;
  uniform float u_speed;
  uniform float u_thickness;

  void main(){
    vHue = aHue;
    vUvV = uv;
    float t = aAngle + u_time * (u_speed * aSpeed) + uv.y * 6.28318; // wrap along length with per-instance variance
    float r = aRadius;
    vec3 pos = vec3(sin(t)*r, cos(t)*r*0.8, 0.0);
    // billboard-ish offset by x across width using camera-space x approx
    vec3 side = normalize(vec3(cos(t), -sin(t)*0.8, 0.0));
    pos += side * ((uv.x - 0.5) * u_thickness * aThick);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`;

export const streamlineFragment = /* glsl */`
  precision highp float;
  varying float vHue;
  varying vec2 vUvV;
  uniform float u_hueShift;
  // simple HSV to RGB
  vec3 hsv2rgb(vec3 c){
    vec4 K = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
  }
  void main(){
    float glow = smoothstep(0.0, 0.2, vUvV.y) * (1.0 - smoothstep(0.8, 1.0, vUvV.y));
    float alpha = smoothstep(0.0, 0.4, glow);
    float hue = fract(vHue + u_hueShift);
    vec3 col = hsv2rgb(vec3(hue, 0.6, 1.0));
    gl_FragColor = vec4(col, alpha);
  }
`;
