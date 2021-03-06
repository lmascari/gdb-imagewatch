#include "stage.hpp"

Stage::Stage()
{
}

bool Stage::initialize(GLCanvas *gl_canvas, uint8_t *buffer, int buffer_width_i, int buffer_height_i, int channels, Buffer::BufferType type, int step, bool ac_enabled) {
    contrast_enabled = ac_enabled;

    std::shared_ptr<GameObject> camera_obj = std::make_shared<GameObject>();
    camera_obj->stage = this;
    camera_obj->add_component("camera_component", std::make_shared<Camera>());
    all_game_objects["camera"] = camera_obj;

    std::shared_ptr<GameObject> buffer_obj = std::make_shared<GameObject>();
    buffer_obj->stage = this;
    buffer_obj->add_component("text_component", std::make_shared<BufferValues>());

    std::shared_ptr<Buffer> buffer_component = std::make_shared<Buffer>();
    buffer_component->buffer = buffer;
    buffer_component->channels = channels;
    buffer_component->type = type;
    buffer_component->buffer_width_f = static_cast<float>(buffer_width_i);
    buffer_component->buffer_height_f = static_cast<float>(buffer_height_i);
    buffer_component->step = step;
    buffer_obj->add_component("buffer_component", buffer_component);

    all_game_objects["buffer"] = buffer_obj;

    for(auto& go: all_game_objects) {
        if(!go.second->initialize(gl_canvas)) {
            return false;
        }
    }

    for(auto& go: all_game_objects) {
        if(!go.second->post_initialize()) {
            return false;
        }
    }

    return true;
}

bool Stage::buffer_update(uint8_t *buffer, int buffer_width_i, int buffer_height_i, int channels, Buffer::BufferType type, int step) {
    GameObject* buffer_obj = all_game_objects["buffer"].get();
    Buffer* buffer_component = buffer_obj->getComponent<Buffer>("buffer_component");

    buffer_component->buffer = buffer;
    buffer_component->channels = channels;
    buffer_component->type = type;
    buffer_component->buffer_width_f = static_cast<float>(buffer_width_i);
    buffer_component->buffer_height_f = static_cast<float>(buffer_height_i);
    buffer_component->step = step;

    for(auto& game_obj_it: all_game_objects) {
        GameObject* game_obj = game_obj_it.second.get();
        game_obj->stage = this;
        for(auto& comp: game_obj->all_components) {
          if(!comp.second->buffer_update()) {
            return false;
          }
        }
    }

    for(auto& game_obj_it: all_game_objects) {
      GameObject* game_obj = game_obj_it.second.get();
      for(auto comp: game_obj->all_components) {
        if(!comp.second->post_buffer_update())
          return false;
      }
    }

    return true;
}

GameObject *Stage::getGameObject(string tag) {
    if(all_game_objects.find(tag) == all_game_objects.end())
        return nullptr;
    return all_game_objects[tag].get();
}

void Stage::update() {
    for(auto& game_obj: all_game_objects)
        game_obj.second->update();
}

void Stage::draw() {
    glClear(GL_COLOR_BUFFER_BIT);

    // TODO use camera tags so I can have multiple cameras (useful for drawing GUI)

    GameObject* camera_obj = all_game_objects["camera"].get();
    Camera* camera_component = camera_obj->getComponent<Camera>("camera_component");

    if(camera_component == nullptr)
        return;

    mat4 viewInv = camera_obj->get_pose().inv();

    for(auto& game_obj: all_game_objects)
        game_obj.second->draw(camera_component->projection, viewInv);
}

void Stage::scroll_callback(float delta) {
    GameObject* cam_obj = all_game_objects["camera"].get();
    Camera* camera_component = cam_obj->getComponent<Camera>("camera_component");
    camera_component->scroll_callback(delta);
}

void Stage::resize_callback(int w, int h) {
    GameObject* cam_obj = all_game_objects["camera"].get();
    Camera* camera_component = cam_obj->getComponent<Camera>("camera_component");
    camera_component->window_resized(w, h);
}

void Stage::mouse_drag_event(int mouse_x, int mouse_y) {
    // Adapt mouse movement with camera rotation
    //mat4 camRot = mat4::rotation(camera->get_angle());
    for(auto& game_obj: all_game_objects) {
        game_obj.second->mouse_drag_event(mouse_x, mouse_y);
    }

}
