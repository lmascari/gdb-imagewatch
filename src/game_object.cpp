#include "game_object.h"

GameObject::GameObject() : scale(1.0, 1.0, 1.0, 0.0),
                           position(0.0, 0.0, 0.0, 1.0),
                           angle(0.0)
{
}

bool GameObject::initialize(GLCanvas *gl_canvas) {
    for(auto comp: all_components) {
        comp.second->game_object = this;
        comp.second->gl_canvas = gl_canvas;
        if(!comp.second->initialize()) {
            return false;
        }
    }
    return true;
}

bool GameObject::post_initialize() {
    for(auto comp: all_components) {
        if(!comp.second->post_initialize())
            return false;
    }
    return true;

}

void GameObject::update() {
    for(auto comp: all_components)
        comp.second->update();
}

void GameObject::draw(const mat4 &projection, const mat4 &viewInv) {
    for(auto& comp: all_components)
        comp.second->draw(projection, viewInv);
}

void GameObject::add_component(const string &component_name, std::shared_ptr<Component> component) {
    all_components[component_name] = component;
}

mat4 GameObject::get_pose()
{
    mat4 pose;
    pose.setFromSRT(scale.x(), scale.y(), scale.z(),
                    angle,
                    position.x(), position.y(), position.z());
    return pose;
}

void GameObject::mouse_drag_event(int mouse_x, int mouse_y) {
    for(auto comp: all_components) {
        comp.second->mouse_drag_event(mouse_x, mouse_y);
    }
}
