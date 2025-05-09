def auto_register_blueprint_routes(app, swagger):
    for blueprint_name, blueprint in app.blueprints.items():
        for endpoint, view_func in blueprint.view_functions.items():
            doc = get_func_doc(view_func)
            if not doc:
                continue

            try:
                rule = next((rule for rule in app.url_map.iter_rules() if rule.endpoint == endpoint), None)
                if not rule:
                    continue

                path = rule.rule
                methods = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
                for method in methods:
                    operation_id = f"{blueprint_name}_{endpoint}_{method.lower()}"
                    swagger.register(
                        view_func,
                        endpoint=endpoint,
                        blueprint=blueprint_name,
                        methods=[method],
                        operation_id=operation_id,
                        parameters=doc.get('parameters', []),
                        responses=doc.get('responses', {}),
                        tags=[blueprint_name],
                    )
                print(f"已注册端点: {endpoint} ({path})")
            except Exception as e:
                print(f"注册端点 {endpoint} 失败: {str(e)}")
