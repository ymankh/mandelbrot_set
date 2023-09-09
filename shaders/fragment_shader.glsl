#version 330

in vec2 v_text;
out vec4 f_color;
uniform sampler2D Texture;
uniform vec2 Center;
uniform float Scale;
uniform float Ratio;
uniform int Iter;
uniform float Power;
uniform int Type;
uniform vec2 JuliaC;

float norm(vec2 z) {
    return z.x * z.x + z.y * z.y;
}
vec2 complexPow(vec2 z, float power, int type) {
    float x = z.x;
    float y = z.y;
    float d = sqrt(x * x + y * y);
    float theta = atan(y / x);
    if(type == 0) {
        return vec2(pow(d, power) * cos(power * theta), pow(d, power) * sin(power * theta));
    }
    if(type == 1) {
        return vec2(pow(d, power) * cos(power * theta), abs(pow(d, power) * sin(power * theta)));
    }
}

vec2 complexMultiply(vec2 z, vec2 w) {
    float x = z.x * w.x - z.y * w.y;
    float y = z.x * w.y + z.y * w.x;
    return vec2(x, y);
}

int fractolEterations(vec2 c, int type) {
    int i;
    vec2 z = c;
    if(Type >= 2 && Type < 4) {
        for(i = 0; i < Iter; i++) {
            z = complexPow(z, Power, type - 2) + JuliaC;
            if(norm(z) > 4.0) {
                break;
            }
        }
        return i;
    }
    if(Type >= 4 && Type < 6) {
        for(i = 0; i < Iter; i++) {
            vec2 w = complexPow(z, Power, type - 4);
            w = vec2(1 - w.x, -w.y);
            vec2 temp = complexMultiply(c, w);
            z = temp;
            if(norm(z) > 4.0) {
                break;
            }
        }
        return i;
    }
    if(Type >= 8 && Type < 10) {
        for(i = 0; i < Iter; i++) {
            vec2 w = complexPow(z, Power, type - 8);
            w = vec2(1 - w.x, -w.y);
            vec2 temp = complexMultiply(c, w);
            z = temp;
            if(norm(z) > 4.0) {
                break;
            }
        }
        return i;
    }
    if(Type >= 6 && Type < 8) {
        for(i = 0; i < Iter; i++) {
            vec2 w = complexPow(z, Power, type - 6);
            w = vec2(1 - w.x, -w.y);
            vec2 temp = complexMultiply(JuliaC, w);
            z = temp;
            if(norm(z) > 4.0) {
                break;
            }
        }
        return i;
    }

    for(i = 0; i < Iter; i++) {
        z = complexPow(z, Power, type) + c;
        if(norm(z) > 4.0) {
            break;
        }
    }
    return i;
}

void main() {
    vec2 c;
    vec2 x = JuliaC;
    c.x = Ratio * v_text.x * Scale - Center.x;
    c.y = v_text.y * Scale - Center.y;
    int i = fractolEterations(c, Type);
    f_color = texture(Texture, vec2((i == Iter ? 0.0 : float(i)) / float(Iter), 0.0));
}